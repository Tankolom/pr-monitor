"""Анализ трека: доли, такты, признаки тактов, матрица «похожести» тактов.

Единица монтажа — такт (или доля, если ритм «плавает»). Склейка между
границами i и j звучит естественно, если такт j похож на такт i (то, что
слушатель ожидал услышать дальше), а предыдущие такты тоже похожи.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

import librosa
import numpy as np

from .io import SR

log = logging.getLogger(__name__)

AN_SR = 22050
HOP = 512

_model = None
_model_lock = threading.Lock()


def _beat_model():
    """Лениво грузим Beat This! (≈80 МБ). Если torch/модели нет — вернём None и возьмём librosa."""
    global _model
    with _model_lock:
        if _model is None:
            try:
                from beat_this.inference import Audio2Beats  # type: ignore

                _model = Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)
            except Exception as e:  # pragma: no cover - зависит от окружения
                log.warning("beat_this unavailable, fallback to librosa: %s", e)
                _model = False
        return _model or None


@dataclass
class Analysis:
    duration: float                 # длительность всего файла, с
    music_start: float              # первый звук (без тишины в начале)
    music_end: float                # последний звук
    beats: np.ndarray               # времена долей
    bounds: np.ndarray              # границы единиц монтажа (тактов/долей), len = n_units + 1
    unit: str                       # "bar" | "beat"
    meter: int                      # долей в такте (оценка)
    tempo: float                    # BPM (медиана)
    rubato: bool                    # темп неровный — монтаж менее надёжен
    dist: np.ndarray = field(repr=False)   # (n, n) нормированная дистанция между единицами
    rms_db: np.ndarray = field(repr=False)  # громкость единиц, дБ
    engine: str = "beat_this"


def _trim_bounds(y_mono: np.ndarray, sr: int) -> tuple[float, float]:
    frame = 1024
    rms = librosa.feature.rms(y=y_mono, frame_length=frame, hop_length=HOP)[0]
    if rms.max() <= 0:
        return 0.0, len(y_mono) / sr
    db = 20 * np.log10(rms / rms.max() + 1e-12)
    idx = np.where(db > -50)[0]
    start = max(0.0, librosa.frames_to_time(idx[0], sr=sr, hop_length=HOP) - 0.02)
    end = min(len(y_mono) / sr, librosa.frames_to_time(idx[-1], sr=sr, hop_length=HOP) + frame / sr)
    return float(start), float(end)


def _track_beats(y_mono: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray, str]:
    model = _beat_model()
    if model is not None:
        beats, downs = model(y_mono, sr)
        return np.asarray(beats, float), np.asarray(downs, float), "beat_this"
    # fallback: librosa + оценка сильной доли по размеру 3 или 4
    tempo, frames = librosa.beat.beat_track(y=y_mono, sr=sr, hop_length=HOP)
    beats = librosa.frames_to_time(frames, sr=sr, hop_length=HOP)
    onset = librosa.onset.onset_strength(y=y_mono, sr=sr, hop_length=HOP)
    strength = onset[np.clip(frames, 0, len(onset) - 1)] if len(frames) else np.array([])
    best = (-1.0, 4, 0)
    for meter in (4, 3):
        for phase in range(meter):
            s = strength[phase::meter].mean() if len(strength[phase::meter]) else 0
            if s > best[0]:
                best = (s, meter, phase)
    _, meter, phase = best
    return beats, beats[phase::meter], "librosa"


def _clean_beats(beats: np.ndarray) -> tuple[np.ndarray, float]:
    """Убирает лишние доли, заполняет провалы (брейки без ударных). Возвращает доли и долю «неровных» интервалов."""
    from scipy.ndimage import median_filter

    b = np.asarray(beats, float)
    if len(b) < 8:
        return b, 1.0
    for _ in range(2):
        ibi = np.diff(b)
        loc = median_filter(ibi, size=9, mode="nearest")
        keep = np.ones(len(b), bool)
        keep[1:][ibi < 0.55 * loc] = False       # слишком близкая доля — ложная
        b = b[keep]
    ibi = np.diff(b)
    loc = median_filter(ibi, size=9, mode="nearest")
    out = [b[0]]
    for k, gap in enumerate(ibi):
        n = int(round(gap / loc[k]))
        if gap > 1.5 * loc[k] and n >= 2:        # провал — достраиваем доли равномерно
            out.extend(b[k] + gap * np.arange(1, n) / n)
        out.append(b[k + 1])
    b = np.array(out)
    ibi = np.diff(b)
    loc = median_filter(ibi, size=9, mode="nearest")
    irregular = float(np.mean(np.abs(ibi / loc - 1) > 0.1))
    return b, irregular


def _meter_by_repetition(beat_feats: np.ndarray) -> int:
    """3 или 4: на каком периоде (в долях) музыка больше похожа сама на себя."""
    f = beat_feats / (np.linalg.norm(beat_feats, axis=1, keepdims=True) + 1e-9)
    n = len(f)

    def sim(lag: int) -> float:
        return float(np.mean(np.sum(f[lag:] * f[:-lag], axis=1))) if n > lag + 8 else 0.0

    three = np.mean([sim(3), sim(6), sim(12)])
    four = np.mean([sim(4), sim(8), sim(16)])
    return 3 if three > four + 0.01 else 4


def _bar_grid(beats: np.ndarray, downs: np.ndarray, beat_feats: np.ndarray | None = None
              ) -> tuple[np.ndarray, int]:
    """Размер + сильные доли по Витерби: позиция доли в такте растёт на 1, сдвиг фазы — редкий и дорогой."""
    if len(beats) < 8:
        return beats[::4], 4
    near = np.zeros(len(beats), bool)
    if len(downs):
        idx = np.clip(np.searchsorted(beats, downs), 1, len(beats) - 1)
        for d, i in zip(downs, idx):
            j = i if abs(beats[i] - d) < abs(beats[i - 1] - d) else i - 1
            if abs(beats[j] - d) < 0.07:
                near[j] = True
    # размер: чаще всего встречающееся число долей между найденными сильными долями
    pos = np.where(near)[0]
    counts = np.diff(pos)
    counts = counts[(counts >= 2) & (counts <= 8)]
    meter = int(np.bincount(counts).argmax()) if len(counts) else 4
    if meter in (6, 8) and np.sum(counts == meter // 2) > 0.6 * np.sum(counts == meter):
        meter //= 2
    share = np.mean(counts == meter) if len(counts) else 0.0
    if beat_feats is not None and (share < 0.45 or meter not in (2, 3, 4, 6)):
        meter = _meter_by_repetition(beat_feats)   # детектор сильных долей сомневается
    if meter == 2:
        meter = 4
    M, n = meter, len(beats)
    SWITCH = 8.0
    emit = np.where(near[:, None], np.r_[0.0, np.ones(M - 1)][None, :], np.r_[0.35, np.zeros(M - 1)][None, :])
    cost = emit[0].copy()
    back = np.zeros((n, M), int)
    for t in range(1, n):
        stay = np.roll(cost, 1)                   # из позиции s-1 в s
        best_any = cost.min()
        take_switch = best_any + SWITCH < stay
        back[t] = np.where(take_switch, cost.argmin(), (np.arange(M) - 1) % M)
        cost = np.minimum(stay, best_any + SWITCH) + emit[t]
    s = int(cost.argmin())
    states = np.zeros(n, int)
    for t in range(n - 1, -1, -1):
        states[t] = s
        s = back[t, s]
    return beats[states == 0], meter


def _unit_features(y_mono: np.ndarray, sr: int, bounds: np.ndarray, sub: int = 4,
                   chroma: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Признаки единицы: хрома + MFCC + громкость, усреднённые по `sub` частям единицы."""
    if chroma is None:
        chroma = librosa.feature.chroma_stft(y=y_mono, sr=sr, hop_length=HOP, n_fft=4096)
    mfcc = librosa.feature.mfcc(y=y_mono, sr=sr, hop_length=HOP, n_mfcc=20)[1:]
    rms = librosa.feature.rms(y=y_mono, hop_length=HOP)[0]
    n_frames = chroma.shape[1]
    t2f = lambda t: int(np.clip(round(t * sr / HOP), 0, n_frames - 1))  # noqa: E731
    feats, loud = [], []
    for a, b in zip(bounds[:-1], bounds[1:]):
        fa, fb = t2f(a), max(t2f(a) + sub, t2f(b))
        edges = np.linspace(fa, fb, sub + 1).astype(int)
        parts = []
        for e0, e1 in zip(edges[:-1], edges[1:]):
            e1 = max(e1, e0 + 1)
            c = chroma[:, e0:e1].mean(axis=1)
            c = c / (np.linalg.norm(c) + 1e-9)
            m = mfcc[:, e0:e1].mean(axis=1)
            parts.append(np.concatenate([c * 3.0, m / 40.0]))
        feats.append(np.concatenate(parts))
        loud.append(20 * np.log10(rms[fa:fb].mean() + 1e-9))
    return np.array(feats), np.array(loud)


def analyze(y: np.ndarray, sr: int = SR) -> Analysis:
    mono = librosa.resample(y.mean(axis=1), orig_sr=sr, target_sr=AN_SR, res_type="soxr_hq")
    duration = len(y) / sr
    start, end = _trim_bounds(mono, AN_SR)
    beats, downs, engine = _track_beats(mono, AN_SR)
    beats = beats[(beats >= start - 0.05) & (beats <= end)]
    downs = downs[(downs >= start - 0.05) & (downs <= end)]
    beats, irregular = _clean_beats(beats)
    ibi = np.diff(beats) if len(beats) > 2 else np.array([0.5])
    tempo = float(60.0 / np.median(ibi))
    rubato = irregular > 0.3 or len(beats) < 16

    chroma = librosa.feature.chroma_stft(y=mono, sr=AN_SR, hop_length=HOP, n_fft=4096)
    if not rubato:
        onset = librosa.onset.onset_strength(y=mono, sr=AN_SR, hop_length=HOP)[None, :]
        frames = librosa.time_to_frames(beats, sr=AN_SR, hop_length=HOP)
        frames = np.clip(frames, 0, chroma.shape[1] - 1)
        bf = librosa.util.sync(np.vstack([chroma, onset / (onset.max() + 1e-9)]), frames, aggregate=np.median).T
        bars, meter = _bar_grid(beats, downs, bf)
        bounds = bars
        if len(bounds) < 6:
            rubato = True
    if not rubato:
        bar_len = float(np.median(np.diff(bounds)))
        bounds = np.append(bounds, min(bounds[-1] + bar_len, end))
        unit = "bar"
    else:
        meter = 4
        # в свободном темпе монтируем по долям, но не чаще 0.35 с
        pts = [start]
        for b in beats:
            if b - pts[-1] >= 0.35:
                pts.append(b)
        if end - pts[-1] > 0.2:
            pts.append(end)
        bounds = np.array(pts)
        unit = "beat"
        if len(bounds) < 8:  # совсем нет ритма — режем по сетке 1 с
            bounds = np.arange(start, end, 1.0)
            bounds = np.append(bounds, end)

    feats, loud = _unit_features(mono, AN_SR, bounds, chroma=chroma)
    # нормализуем признаки и считаем попарные расстояния
    f = (feats - feats.mean(axis=0)) / (feats.std(axis=0) + 1e-6)
    sq = (f ** 2).sum(axis=1)
    d = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * f @ f.T, 0)) / np.sqrt(f.shape[1])
    off = d[~np.eye(len(d), dtype=bool)]
    scale = np.median(off) if len(off) else 1.0
    d = d / (scale + 1e-9)
    return Analysis(duration=duration, music_start=start, music_end=end, beats=beats, bounds=bounds,
                    unit=unit, meter=meter, tempo=tempo, rubato=rubato, dist=d, rms_db=loud, engine=engine)

"""Сборка звука по плану: подстройка стыков, кроссфейды, темп, громкость, сигнал, водяной знак."""
from __future__ import annotations

import threading

import librosa
import numpy as np
import pyloudnorm as pyln

from .io import SR, stretch_to_duration
from .planner import Plan

TARGET_LUFS = -14.0
PEAK_CEIL = 10 ** (-1.0 / 20)   # -1 dBFS
SIGNAL_LEAD = 2.0               # сигнал за 2 с до начала музыки


def _onset_env(x: np.ndarray, sr: int, hop: int) -> np.ndarray:
    """Грубая огибающая атак: положительный прирост энергии в полосах (быстро, без librosa)."""
    n = len(x) // hop
    if n < 3:
        return np.zeros(max(n, 1))
    frames = x[: n * hop].reshape(n, hop)
    spec = np.abs(np.fft.rfft(frames * np.hanning(hop), axis=1))
    bands = np.add.reduceat(spec, np.unique(np.geomspace(1, spec.shape[1] - 1, 24).astype(int)), axis=1)
    lg = np.log1p(bands * 10)
    return np.maximum(np.diff(lg, axis=0, prepend=lg[:1]), 0).sum(axis=1)


def _refine_offset(mono: np.ndarray, a: int, b: int, sr: int, coarse: float = 0.07, fine: float = 0.006,
                   win: float = 1.2) -> int:
    """Сдвиг точки входа b (в сэмплах): сначала совмещаем атаки (±70 мс), затем фазу волны (±6 мс).

    `a` — где «должно было» продолжиться звучание, `b` — откуда реально продолжаем.
    """
    hop = int(0.005 * sr)
    L = int(win * sr)
    S = int(coarse * sr)
    shift = 0
    if a >= 0 and b - S >= 0 and a + L < len(mono) and b + S + L < len(mono):
        ea = _onset_env(mono[a:a + L], sr, hop)
        eb = _onset_env(mono[b - S:b + S + L], sr, hop)
        ea = ea - ea.mean()
        best, best_k = -np.inf, 0
        k_max = len(eb) - len(ea)
        for k in range(0, k_max + 1):
            seg = eb[k:k + len(ea)]
            c = float(np.dot(seg - seg.mean(), ea))
            # небольшое предпочтение нулевому сдвигу: трекер обычно прав
            c -= abs(k * hop - S) / S * 0.1 * (np.abs(ea).sum() + 1e-9)
            if c > best:
                best, best_k = c, k
        shift = best_k * hop - S
    # тонкая подстройка по форме волны вокруг найденной точки
    s, w = int(fine * sr), int(0.05 * sr)
    bb = b + shift
    if a + w >= len(mono) or bb - s < 0 or bb + s + w >= len(mono):
        return shift
    ref = mono[a:a + w] - mono[a:a + w].mean()
    seg = mono[bb - s:bb + s + w]
    corr = np.correlate(seg - seg.mean(), ref, mode="valid")
    energy = np.sqrt(np.convolve(seg ** 2, np.ones(w), mode="valid") * (ref ** 2).sum()) + 1e-9
    return shift + int(np.argmax(corr / energy)) - s


def assemble(y: np.ndarray, plan: Plan, xfade: float = 0.06, sr: int = SR,
             offsets: dict[int, int] | None = None) -> tuple[np.ndarray, list[float]]:
    """Склеивает отрезки плана. Возвращает звук и времена стыков (в секундах результата).

    Стык i→j: звучит A до точки (b_i − pre − X), затем за X сэмплов A затухает, а B
    (с точки a_j − pre − X) нарастает; к сильной доле B звучит уже только B.
    """
    mono = y.mean(axis=1)
    X = max(int(xfade * sr), 16)
    pre = int(0.012 * sr)   # стык чуть раньше сильной доли, чтобы атака была «чистой»
    segs = [(int(round(a * sr)), int(round(b * sr))) for a, b in plan.segments]
    starts = [segs[0][0]]
    for k in range(1, len(segs)):
        a = segs[k][0]
        tail_src = segs[k - 1][1] - pre - X
        extra = (offsets or {}).get(k - 1, 0)          # ручной сдвиг стыка k-1 (самопроверка ритма)
        a += extra
        a += _refine_offset(mono, tail_src, a - pre - X, sr)
        starts.append(max(a, X + pre))
    out: list[np.ndarray] = []
    seam_times: list[float] = []
    cursor = 0
    t = np.linspace(0, np.pi / 2, X, dtype=np.float32)
    last = len(segs) - 1
    for k, ((_, end), start) in enumerate(zip(segs, starts)):
        seg_start = start - pre - X if k > 0 else start
        seg_end = end if k == last else end - pre - X
        body = y[seg_start:seg_end].copy()
        if k > 0:
            tail_src = segs[k - 1][1] - pre - X
            tail = y[tail_src:tail_src + X]
            n = min(X, len(body), len(tail))
            a_ref, b_ref = tail[:n].mean(axis=1), body[:n].mean(axis=1)
            coherent = 0.0
            if n > 10 and a_ref.std() > 1e-6 and b_ref.std() > 1e-6:
                coherent = float(np.corrcoef(a_ref, b_ref)[0, 1])
            if coherent > 0.6:   # похожие сигналы — линейный кроссфейд не даёт «горба»
                fin = np.linspace(0, 1, n, dtype=np.float32)
                fout = 1 - fin
            else:                # несвязанные — равная мощность
                fin = np.sin(t[:n])
                fout = np.cos(t[:n])
            body[:n] = body[:n] * fin[:, None] + tail[:n] * fout[:, None]
            seam_times.append((cursor + n) / sr)
        out.append(body)
        cursor += len(body)
    return (np.concatenate(out) if out else y[:0]), seam_times


def loudness_normalize(y: np.ndarray, sr: int = SR) -> np.ndarray:
    meter = pyln.Meter(sr)
    try:
        lufs = meter.integrated_loudness(y.astype(np.float64))
    except ValueError:
        lufs = -np.inf
    gain = 1.0
    if np.isfinite(lufs):
        gain = 10 ** ((TARGET_LUFS - lufs) / 20)
    peak = np.abs(y).max() + 1e-9
    gain = min(gain, PEAK_CEIL / peak, 10 ** (12 / 20))  # не выше -1 dBFS и не громче +12 дБ
    return (y * gain).astype(np.float32)


def fades(y: np.ndarray, fade_in: float = 0.005, fade_out: float = 0.03, sr: int = SR) -> np.ndarray:
    y = y.copy()
    n_in, n_out = int(fade_in * sr), int(fade_out * sr)
    if n_in:
        y[:n_in] *= np.linspace(0, 1, n_in, dtype=np.float32)[:, None]
    if n_out and n_out < len(y):
        curve = np.cos(np.linspace(0, np.pi / 2, n_out, dtype=np.float32)) ** 2
        y[-n_out:] *= curve[:, None]
    return y


def fix_length(y: np.ndarray, seconds: float, sr: int = SR) -> np.ndarray:
    n = int(round(seconds * sr))
    if len(y) > n:
        return y[:n]
    if len(y) < n:
        return np.pad(y, ((0, n - len(y)), (0, 0)))
    return y


def signal(sr: int = SR) -> np.ndarray:
    """Короткий «пик» 1 кГц и тишина до музыки: всего SIGNAL_LEAD секунд."""
    n = int(0.3 * sr)
    t = np.arange(n) / sr
    env = np.minimum(1, np.minimum(t / 0.01, (0.3 - t) / 0.02))
    tone = 0.5 * np.sin(2 * np.pi * 1000 * t) * env
    lead = np.zeros((int(SIGNAL_LEAD * sr), 2), dtype=np.float32)
    lead[:n] = tone[:, None]
    return lead


def watermark(y: np.ndarray, avoid: list[float], every: float = 11.0, sr: int = SR) -> np.ndarray:
    """Превью: тихие двойные «блипы» каждые ~11 с, не ближе 2 с к стыкам и к финалу."""
    y = y.copy()
    dur = len(y) / sr
    n = int(0.07 * sr)
    t = np.arange(n) / sr
    blip = (np.sin(2 * np.pi * 1760 * t) * np.hanning(n)).astype(np.float32)
    level = 0.18 * (np.sqrt(np.mean(y ** 2)) / 0.1 + 0.2)
    level = float(np.clip(level, 0.05, 0.35))
    pos = 4.0
    while pos < dur - 3.0:
        if all(abs(pos - s) > 2.0 for s in avoid):
            for off in (0.0, 0.12):
                i = int((pos + off) * sr)
                if i + n < len(y):
                    y[i:i + n] += level * blip[:, None]
        pos += every
    return np.clip(y, -1, 1)


_check_lock = threading.Lock()


def seam_phase_error(audio: np.ndarray, t: float, sr: int = SR) -> tuple[float | None, float]:
    """Сбой ритма на стыке: доли после t против сетки, продолженной из долей до t (0 — идеально, 0.5 — полдоли).

    Возвращает (ошибка или None, если ритм не найден; средний межударный интервал).
    """
    from .analysis import AN_SR, _beat_model

    a, b = max(int((t - 6) * sr), 0), min(int((t + 4) * sr), len(audio))
    if b - a < 4 * sr:
        return None, 0.5
    seg = librosa.resample(audio[a:b].mean(axis=1), orig_sr=sr, target_sr=AN_SR, res_type="soxr_mq")
    model = _beat_model()
    if model is None:
        return None, 0.5
    with _check_lock:
        beats, _ = model(seg, AN_SR)
    beats = np.asarray(beats) + a / sr
    pre = beats[(beats > t - 4) & (beats < t - 0.05)]
    post = beats[(beats > t + 0.05) & (beats < t + 3)][:4]
    if len(pre) < 4 or len(post) < 2:
        return None, 0.5
    step = float(np.median(np.diff(pre)))
    phase = ((post - pre[-1]) / step) % 1.0
    return float(np.median(np.minimum(phase, 1 - phase))), step


RHYTHM_BAD = 0.2


def assemble_checked(y: np.ndarray, plan: Plan, xfade: float, sr: int = SR
                     ) -> tuple[np.ndarray, list[float], list[float | None]]:
    """Склейка + самопроверка ритма на каждом стыке; при сбое пробует сдвиги на ±¼ и ±½ доли."""
    offsets: dict[int, int] = {}
    audio, seams = assemble(y, plan, xfade=xfade, sr=sr)
    errors: list[float | None] = []
    for k in range(len(seams)):
        err, step = seam_phase_error(audio, seams[k], sr)
        if err is not None and err > RHYTHM_BAD:
            best = (err, 0, audio, seams)
            for frac in (0.5, -0.5, 0.25, -0.25):
                trial = dict(offsets)
                trial[k] = int(round(frac * step * sr))
                a2, s2 = assemble(y, plan, xfade=xfade, sr=sr, offsets=trial)
                e2, _ = seam_phase_error(a2, s2[k], sr)
                if e2 is not None and e2 < best[0] - 0.05:
                    best = (e2, trial[k], a2, s2)
            err = best[0]
            if best[1]:
                offsets[k] = best[1]
                audio, seams = best[2], best[3]
        errors.append(err)
    return audio, seams, errors


def render(y: np.ndarray, plan: Plan, target: float, *, with_signal: bool, xfade: float, sr: int = SR,
           check_rhythm: bool = True) -> tuple[np.ndarray, list[float]]:
    """Полный рендер варианта. Возвращает звук точно нужной длины и времена стыков.

    Результат самопроверки ритма записывается в plan.rhythm_errors.
    """
    if check_rhythm and plan.seams and plan.kind != "fade":
        audio, seams, plan.rhythm_errors = assemble_checked(y, plan, xfade, sr)
    else:
        audio, seams = assemble(y, plan, xfade=xfade, sr=sr)
    ratio = target / (len(audio) / sr)
    audio = stretch_to_duration(audio, target, sr)
    seams = [s * ratio for s in seams]
    audio = fix_length(audio, target, sr)
    if plan.fade_out > 0:
        n = int(plan.fade_out * sr)
        curve = np.cos(np.linspace(0, np.pi / 2, n, dtype=np.float32)) ** 2
        audio[-n:] *= curve[:, None]
    audio = fades(audio)
    audio = loudness_normalize(audio, sr)
    if with_signal:
        audio = np.concatenate([signal(sr), audio])
        seams = [s + SIGNAL_LEAD for s in seams]
    return audio, seams


def peaks(y: np.ndarray, points: int = 600) -> list[float]:
    mono = np.abs(y).max(axis=1)
    edges = np.linspace(0, len(mono), points + 1).astype(int)
    vals = np.array([mono[a:b].max() if b > a else 0 for a, b in zip(edges[:-1], edges[1:])])
    m = vals.max() or 1
    return [round(float(v / m), 3) for v in vals]

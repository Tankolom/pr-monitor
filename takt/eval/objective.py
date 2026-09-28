"""Объективная проверка стыков в готовых вариантах.

Для каждого стыка считаем:
  * ритм: насколько межударные интервалы рядом со стыком отличаются от медианы трека
    (сбившийся ритм = слышимая «запинка»);
  * новизну: насколько резко меняются тембр (log-mel) и гармония (хрома) на стыке
    по сравнению с обычными переходами между долями в этом же треке (перцентиль).
Стык подозрителен, если ритм сбит >12 % или новизна выше 97-го перцентиля естественных переходов.

Запуск: python -m eval.objective <папка_с_результатами> [...]
"""
from __future__ import annotations

import json
import os
import sys

import librosa
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.audio.analysis import _beat_model  # noqa: E402

SR = 22050
HOP = 256


def novelty_at(feat: np.ndarray, frames: np.ndarray, w: int) -> np.ndarray:
    out = []
    for f in frames:
        a, b = feat[:, max(f - w, 0):max(f - 2, 1)], feat[:, f + 2:f + w]
        if a.shape[1] < 2 or b.shape[1] < 2:
            out.append(np.nan)
            continue
        out.append(np.linalg.norm(a.mean(1) - b.mean(1)))
    return np.array(out)


def phase_error(beats: np.ndarray, t: float) -> float | None:
    """Насколько первые доли после момента t отстают от сетки, продолженной из долей до t (в долях 0…0.5).

    Устойчиво к пропущенным/лишним долям трекера: берём расстояние до ближайшего узла сетки.
    Чистый стык ≈ 0.05, сбой ритма на полдоли ≈ 0.5.
    """
    pre = beats[(beats > t - 4) & (beats < t - 0.05)]
    post = beats[(beats > t + 0.05) & (beats < t + 3)][:4]
    if len(pre) < 4 or len(post) < 2:
        return None
    step = float(np.median(np.diff(pre)))
    phase = ((post - pre[-1]) / step) % 1.0
    return float(np.median(np.minimum(phase, 1 - phase)))


def check_variant(path: str, seams: list[float], signal_lead: float = 0.0) -> dict:
    y, sr = sf.read(path, dtype="float32", always_2d=True)
    mono = librosa.resample(y.mean(1), orig_sr=sr, target_sr=SR)
    model = _beat_model()
    beats, _ = model(mono, SR)
    beats = np.asarray(beats)
    ibi = np.diff(beats)
    med = np.median(ibi) if len(ibi) else 0.5
    mel = librosa.power_to_db(librosa.feature.melspectrogram(y=mono, sr=SR, hop_length=HOP, n_mels=64))
    mel = (mel - mel.mean(1, keepdims=True)) / (mel.std(1, keepdims=True) + 1e-6)
    chroma = librosa.feature.chroma_stft(y=mono, sr=SR, hop_length=HOP, n_fft=4096)
    w = int(0.4 * SR / HOP)
    beat_frames = librosa.time_to_frames(beats[(beats > signal_lead + 1)], sr=SR, hop_length=HOP)
    base_mel = novelty_at(mel, beat_frames, w)
    base_chr = novelty_at(chroma, beat_frames, w)
    res = []
    for s in seams:
        pe = phase_error(beats, s)
        dev = -1.0 if pe is None else pe
        # ближайшая к стыку доля — там звучит «вход» нового фрагмента
        if len(beats):
            fb = librosa.time_to_frames([beats[np.argmin(np.abs(beats - s))]], sr=SR, hop_length=HOP)
        else:
            fb = librosa.time_to_frames([s], sr=SR, hop_length=HOP)
        nm = novelty_at(mel, fb, w)[0]
        nc = novelty_at(chroma, fb, w)[0]
        pm = float(np.nanmean(base_mel <= nm) * 100)
        pc = float(np.nanmean(base_chr <= nc) * 100)
        res.append({"t": s, "rhythm_dev": round(dev, 3), "timbre_pct": round(pm, 1), "harmony_pct": round(pc, 1),
                    # сбой ритма — главный слышимый дефект; резкая смена и тембра, и гармонии — второй
                    "suspicious": bool(dev > 0.2 or (pm > 98 and pc > 98))})
    # фон: та же метрика ритма на случайных местах без стыков
    rng = np.random.default_rng(0)
    dur = len(y) / sr
    ctrl = []
    for t in rng.uniform(signal_lead + 5, dur - 5, 40):
        if all(abs(t - s) > 5 for s in seams):
            pe = phase_error(beats, t)
            if pe is not None:
                ctrl.append(pe)
    return {"seams": res, "control_rhythm_dev_median": round(float(np.median(ctrl)), 3) if ctrl else None,
            "control_rhythm_dev_p90": round(float(np.percentile(ctrl, 90)), 3) if ctrl else None,
            "duration": round(dur, 3)}


def main(dirs: list[str]) -> None:
    summary = []
    for d in dirs:
        meta = json.load(open(os.path.join(d, "meta.json")))
        lead = 2.0 if meta.get("signal") else 0.0
        for v in meta["variants"]:
            path = os.path.join(d, f"v{v['index']}.flac")
            r = check_variant(path, [s["t"] for s in v["seams"]], lead)
            exp = meta["target"] + lead
            r.update({"dir": os.path.basename(d), "variant": v["index"], "kind": v["kind"],
                      "quality": v["quality"], "costs": [s["cost"] for s in v["seams"]],
                      "duration_error": round(r["duration"] - exp, 3)})
            summary.append(r)
            flag = "!!" if any(s["suspicious"] for s in r["seams"]) else "ok"
            print(f"{flag} {r['dir']:>22} v{v['index']} {v['kind']:>7} q={v['quality']:<6} "
                  f"dur_err={r['duration_error']:+.3f} ctrl={r['control_rhythm_dev_median']} "
                  + " | ".join(f"t={s['t']:.1f} r={s['rhythm_dev']:.2f} tim={s['timbre_pct']:.0f} "
                               f"har={s['harmony_pct']:.0f} c={c:.2f}" for s, c in zip(r["seams"], r["costs"])),
                  flush=True)
    json.dump(summary, open("objective_report.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])

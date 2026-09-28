"""Прогон набора треков через движок + объективная проверка стыков + спектрограммы.

python -m eval.run_eval --music <папка с треками> --out <папка результатов> [--targets 90,150] [--jobs 2]

Итог: <out>/summary.md и <out>/<трек>_<длит>/seam_*.png (±3 с вокруг каждого стыка).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _one(args):
    src, out, target = args
    import torch

    torch.set_num_threads(2)
    from app.audio.pipeline import Options, process

    t0 = time.time()
    try:
        meta = process(src, out, Options(target=target))
    except Exception as e:  # noqa: BLE001
        return {"src": src, "target": target, "error": repr(e)}
    return {"src": src, "target": target, "out": out, "elapsed": round(time.time() - t0, 1), "meta": meta}


def spectro(path: str, t: float, png: str, title: str) -> None:
    import librosa
    import librosa.display
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import soundfile as sf

    y, sr = sf.read(path, dtype="float32", always_2d=True)
    a, b = max(int((t - 3) * sr), 0), min(int((t + 3) * sr), len(y))
    seg = librosa.resample(y[a:b].mean(1), orig_sr=sr, target_sr=22050)
    S = librosa.power_to_db(librosa.feature.melspectrogram(y=seg, sr=22050, n_mels=96), ref=1.0)
    fig, ax = plt.subplots(figsize=(7, 2.6), dpi=90)
    librosa.display.specshow(S, sr=22050, x_axis="time", y_axis="mel", ax=ax, cmap="magma")
    ax.axvline(t - a / sr, color="cyan", lw=1.2)
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(png)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--music", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--targets", default="90")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--no-objective", action="store_true")
    a = ap.parse_args()
    files = sorted(sum((glob.glob(os.path.join(a.music, e)) for e in ("*.mp3", "*.wav", "*.flac", "*.ogg", "*.m4a")), []))
    tasks = []
    for f in files:
        for t in [float(x) for x in a.targets.split(",")]:
            name = f"{os.path.splitext(os.path.basename(f))[0]}_{int(t)}"
            tasks.append((f, os.path.join(a.out, name), t))
    os.makedirs(a.out, exist_ok=True)
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        results = list(ex.map(_one, tasks))
    rows = []
    from eval.objective import check_variant

    for r in results:
        if "error" in r:
            rows.append(f"| {os.path.basename(r['src'])} | {int(r['target'])} | ОШИБКА {r['error'][:80]} | | | |")
            continue
        meta = r["meta"]
        for v in meta["variants"]:
            path = os.path.join(r["out"], f"v{v['index']}.flac")
            seams = [s["t"] for s in v["seams"]]
            obj = {"seams": []}
            if not a.no_objective and seams:
                obj = check_variant(path, seams, 2.0 if meta.get("signal") else 0.0)
            for k, s in enumerate(seams):
                spectro(path, s, os.path.join(r["out"], f"v{v['index']}_seam{k}.png"),
                        f"{os.path.basename(r['out'])} v{v['index']} seam {k} t={s:.1f} cost={v['seams'][k]['cost']}")
            sus = sum(1 for s in obj["seams"] if s["suspicious"])
            det = "; ".join(f"r={s['rhythm_dev']:.2f} tim={s['timbre_pct']:.0f} har={s['harmony_pct']:.0f}" for s in obj["seams"])
            rows.append(f"| {os.path.basename(r['out'])} | v{v['index']} {v['kind']} | {v['quality']} | "
                        f"{v['tempo_change']:+.2f}% | {', '.join(str(s['cost']) for s in v['seams'])} | "
                        f"{'⚠ ' * sus}{det} | {r['elapsed']}s |")
    head = ("| трек | вариант | оценка | темп | стоимость стыков | объективно (ритм, тембр‰, гармония‰) | время |\n"
            "|---|---|---|---|---|---|---|\n")
    with open(os.path.join(a.out, "summary.md"), "w") as f:
        f.write(head + "\n".join(rows) + "\n")
    json.dump([{k: v for k, v in r.items() if k != "meta"} for r in results], open(os.path.join(a.out, "runs.json"), "w"))
    print(head + "\n".join(rows))


if __name__ == "__main__":
    main()

"""Полный цикл: исходный файл → 3 варианта нужной длины (+ превью с водяным знаком)."""
from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable

import soundfile as sf

from . import io
from .analysis import analyze
from .io import SR, AudioError
from .planner import make_plans, plan_fade
from .render import peaks, render, watermark

log = logging.getLogger(__name__)

MIN_TARGET, MAX_TARGET = 20.0, 600.0
MAX_SOURCE = 12 * 60.0
MAX_EXTEND_RATIO = 3.0

# пороги заметности стыка (калиброваны на тестовом наборе, см. eval/)
SEAM_GREAT = 0.55
SEAM_OK = 0.85


@dataclass
class Options:
    target: float                 # нужная длительность музыки, с
    ending: str = "natural"       # natural | fade
    signal: bool = False          # «пик» перед музыкой (в длительность не входит)
    tempo: float = 1.0            # 0.85…1.15 — изменить темп всего трека

    def validate(self) -> None:
        if not (MIN_TARGET <= self.target <= MAX_TARGET):
            raise AudioError(f"Длительность должна быть от {int(MIN_TARGET)} с до {int(MAX_TARGET // 60)} мин.")
        if self.ending not in ("natural", "fade"):
            raise AudioError("Неизвестный вариант финала.")
        if not (0.85 <= self.tempo <= 1.15):
            raise AudioError("Темп можно менять не больше чем на 15 %.")


def seam_quality(cost: float) -> str:
    return "great" if cost < SEAM_GREAT else ("ok" if cost < SEAM_OK else "check")


def fmt_time(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}"


def process(src: str, out_dir: str, opts: Options, progress: Callable[[int, str], None] | None = None) -> dict:
    t0 = time.time()
    step = progress or (lambda p, m: None)
    opts.validate()
    info = io.probe(src)
    if info["duration"] and info["duration"] > MAX_SOURCE:
        raise AudioError("Трек длиннее 12 минут. Обрежьте его или загрузите другой файл.")
    step(5, "Читаем файл")
    y = io.decode(src)
    if float(abs(y).max()) < 10 ** (-60 / 20):
        raise AudioError("В файле тишина или очень тихий звук. Проверьте, тот ли файл загружен.")
    if opts.tempo != 1.0:
        step(10, "Меняем темп")
        y = io.stretch_to_duration(y, len(y) / SR / opts.tempo)
    step(15, "Ищем такты и доли")
    an = analyze(y)
    L = an.music_end - an.music_start
    if L < 8:
        raise AudioError("В файле почти нет музыки (тишина или очень тихо).")
    if opts.target > L * MAX_EXTEND_RATIO:
        raise AudioError(f"Слишком большое удлинение: трек звучит {fmt_time(L)}, "
                         f"а нужно {fmt_time(opts.target)}. Можно удлинить не больше чем в 3 раза.")
    step(45, "Подбираем места склеек")
    plans = make_plans(an, opts.target, n=3, ending=opts.ending)
    xfade = 0.18 if an.rubato else 0.06
    os.makedirs(out_dir, exist_ok=True)
    step(55, "Собираем варианты")

    def build(k: int, plan) -> dict | None:
        if abs(plan.stretch - 1) > 0.12:
            return None  # такой вариант звучал бы заметно быстрее/медленнее — не показываем
        audio, seams = render(y, plan, opts.target, with_signal=opts.signal, xfade=xfade)
        sf.write(os.path.join(out_dir, f"v{k}.flac"), audio, SR, subtype="PCM_24")
        io.encode(watermark(audio, seams), os.path.join(out_dir, f"v{k}_preview.mp3"), bitrate="128k")
        return {
            "index": k,
            "kind": plan.kind,
            "duration": round(len(audio) / SR, 3),
            "music_duration": round(opts.target, 3),
            # сжали трек → темп вырос на столько же
            "tempo_change": round((plan.stretch - 1) * 100, 2),
            "seams": [{"t": round(s, 2), "quality": seam_quality(c), "cost": round(c, 3),
                       "from": round(float(an.bounds[i]), 2), "to": round(float(an.bounds[j]), 2)}
                      for s, c, (i, j) in zip(seams, plan.seam_costs, plan.seams)],
            "fade_out": plan.fade_out,
            "quality": _variant_quality(plan, an.rubato),
            "rhythm": [None if e is None else round(e, 3) for e in plan.rhythm_errors],
            "score": plan.score,
            "peaks": peaks(audio),
        }

    # варианты собираются параллельно: основное время — внешние rubberband/ffmpeg
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = [ex.submit(build, k, plan) for k, plan in enumerate(plans)]
        variants = [v for v in (f.result() for f in futures) if v is not None]
    # варианты со сбитым ритмом — вниз списка; очень заметные стыки не показываем, если есть из чего выбрать
    order = {"great": 0, "ok": 1, "fade": 2, "check": 3}
    variants.sort(key=lambda v: (order[v["quality"]], v["score"]))
    good = [v for v in variants if v["quality"] != "check"]
    if good:
        variants = good + [v for v in variants if v["quality"] == "check" and v["score"] < 1.1][: max(0, 3 - len(good))]
    # мало хороших вариантов — добавим честный запасной: начало трека + затухание
    if len(variants) < 3 and L > opts.target and not any(v["kind"] == "fade" for v in variants):
        extra = build(len(plans), plan_fade(an, opts.target))
        if extra:
            variants.append(extra)
    for v in variants:
        v.pop("score", None)
    if not variants:
        raise AudioError("Не получилось собрать вариант нужной длины. Попробуйте другую длительность.")
    meta = {
        "source_duration": round(an.duration, 2),
        "music_start": round(an.music_start, 2),
        "music_end": round(an.music_end, 2),
        "tempo": round(an.tempo, 1),
        "meter": an.meter,
        "unit": an.unit,
        "rubato": an.rubato,
        "engine": an.engine,
        "signal": opts.signal,
        "target": opts.target,
        "variants": variants,
        "elapsed": round(time.time() - t0, 1),
    }
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False)
    step(100, "Готово")
    return meta


def _variant_quality(plan, rubato: bool) -> str:
    if plan.kind == "fade":
        return "fade"
    if any(e is not None and e > 0.2 for e in plan.rhythm_errors):
        return "check"
    if plan.kind == "stretch":
        return "great" if abs(plan.stretch - 1) <= 0.03 else "check"
    worst = max(plan.seam_costs) if plan.seam_costs else 0
    q = seam_quality(worst)
    if rubato and q == "great":
        q = "ok"
    return q


def export(out_dir: str, index: int, fmt: str, title: str) -> str:
    """Готовит файл для скачивания (MP3 320 кбит/с или WAV 16 бит) из сохранённого FLAC."""
    src = os.path.join(out_dir, f"v{index}.flac")
    dst = os.path.join(out_dir, f"v{index}.{fmt}")
    if not os.path.exists(dst):
        y, _ = sf.read(src, dtype="float32", always_2d=True)
        tmp = dst + ".tmp"
        if fmt == "wav":
            sf.write(tmp, y, SR, subtype="PCM_16", format="WAV")
        else:
            io.encode(y, tmp + ".mp3", bitrate="320k", title=title)
            os.replace(tmp + ".mp3", tmp)
        os.replace(tmp, dst)
    return dst


def load_meta(out_dir: str) -> dict:
    with open(os.path.join(out_dir, "meta.json")) as f:
        return json.load(f)


__all__ = ["Options", "process", "export", "load_meta", "AudioError"]

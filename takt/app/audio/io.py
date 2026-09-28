"""Decoding/encoding через ffmpeg. Внутри движка звук — float32 массив (samples, 2), 44.1 кГц."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf

SR = 44100


class AudioError(Exception):
    """Файл не удалось прочитать как аудио. Сообщение показывается пользователю."""


def probe(path: str) -> dict:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output=True, check=True, timeout=60,
        ).stdout
        info = json.loads(out)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
        raise AudioError("Не получилось прочитать файл. Загрузите MP3, M4A, WAV, OGG или FLAC.") from None
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if not streams:
        raise AudioError("В файле нет звуковой дорожки.")
    try:
        duration = float(info.get("format", {}).get("duration") or streams[0].get("duration") or 0)
    except ValueError:
        duration = 0.0
    return {"duration": duration, "codec": streams[0].get("codec_name"), "channels": streams[0].get("channels")}


def decode(path: str, sr: int = SR) -> np.ndarray:
    try:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vn", "-f", "f32le", "-acodec", "pcm_f32le",
             "-ac", "2", "-ar", str(sr), "pipe:1"],
            capture_output=True, check=True, timeout=180,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise AudioError("Не получилось декодировать файл. Попробуйте другой формат (MP3 или WAV).") from None
    y = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
    if len(y) < sr * 5:
        raise AudioError("Файл слишком короткий: нужно хотя бы 5 секунд музыки.")
    return y


def encode(y: np.ndarray, path: str, fmt: str = "mp3", bitrate: str = "320k", sr: int = SR,
           title: str | None = None) -> None:
    y = np.clip(y, -1.0, 1.0).astype(np.float32)
    if fmt == "wav":
        sf.write(path, y, sr, subtype="PCM_16")
        return
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", "pipe:0",
           "-codec:a", "libmp3lame", "-b:a", bitrate]
    if title:
        cmd += ["-metadata", f"title={title}"]
    cmd.append(path)
    subprocess.run(cmd, input=y.tobytes(), check=True, capture_output=True, timeout=180)


def stretch_to_duration(y: np.ndarray, seconds: float, sr: int = SR) -> np.ndarray:
    """Меняет темп без изменения высоты (Rubber Band R2 — быстрый и чистый на малых изменениях) так, чтобы длительность стала `seconds`."""
    current = len(y) / sr
    if abs(current - seconds) < 0.002:
        return y
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        sf.write(src, y, sr, subtype="FLOAT")
        subprocess.run(["rubberband", "-q", "--threads", "-D", f"{seconds:.6f}", src, dst],
                       check=True, capture_output=True, timeout=300)
        out, _ = sf.read(dst, dtype="float32", always_2d=True)
    return out

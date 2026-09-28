import os
import sys

import numpy as np
import pytest
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SR = 44100
BPM = 120.0
BAR = 4 * 60 / BPM  # 2 секунды


def _tone(freqs, dur, sr=SR, amp=0.12):
    t = np.arange(int(dur * sr)) / sr
    env = np.minimum(1, t / 0.01) * np.exp(-t * 1.5)
    x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) for f in freqs)
    return (amp * x * env).astype(np.float32)


def _kick(sr=SR):
    t = np.arange(int(0.25 * sr)) / sr
    f = 120 * np.exp(-t * 18) + 40
    return (0.8 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 14)).astype(np.float32)


def _snare(sr=SR, seed=0):
    t = np.arange(int(0.18 * sr)) / sr
    rng = np.random.default_rng(seed)
    return (0.35 * rng.standard_normal(len(t)) * np.exp(-t * 25)).astype(np.float32)


def _hat(sr=SR, seed=1):
    t = np.arange(int(0.05 * sr)) / sr
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(len(t))
    n = np.diff(n, prepend=0)
    return (0.12 * n * np.exp(-t * 80)).astype(np.float32)


def make_song(seconds_ending: float = 3.0) -> np.ndarray:
    """Песня 120 уд/мин, 4/4: A B A B A (по 8 тактов) + финальный аккорд. Длительность ≈ 83 с."""
    A = [[261.6, 329.6, 392.0], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6]]
    B = [[293.7, 349.2, 440.0], [329.6, 415.3, 493.9], [220.0, 277.2, 329.6], [246.9, 311.1, 370.0]]
    sections = [A, B, A, B, A]
    total = len(sections) * 8 * BAR + seconds_ending
    y = np.zeros(int(total * SR) + SR, np.float32)
    beat = 60 / BPM
    kick, snare, hat = _kick(), _snare(), _hat()

    def add(sig, t):
        i = int(t * SR)
        y[i:i + len(sig)] += sig[: len(y) - i]

    bar_i = 0
    for sec_idx, sec in enumerate(sections):
        for k in range(8):
            t0 = bar_i * BAR
            chord = sec[k % 4]
            add(_tone(chord, BAR), t0)
            add(_tone([chord[0] / 2], BAR, amp=0.2), t0)
            for b in range(4):
                tb = t0 + b * beat
                if b in (0, 2):
                    add(kick, tb)
                else:
                    add(snare, tb)
                if sec is B or sec_idx == 4:
                    add(hat, tb)
                    add(hat, tb + beat / 2)
            bar_i += 1
    add(_tone([261.6, 329.6, 392.0, 523.2], seconds_ending, amp=0.15), bar_i * BAR)
    add(kick, bar_i * BAR)
    y = y[: int(total * SR)]
    y = y / np.abs(y).max() * 0.8
    return np.stack([y, y], axis=1)


@pytest.fixture(scope="session")
def song_path(tmp_path_factory):
    d = tmp_path_factory.mktemp("audio")
    p = str(d / "song.wav")
    sf.write(p, make_song(), SR, subtype="PCM_16")
    return p


@pytest.fixture()
def app_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("BASE_URL", "http://testserver")
    monkeypatch.setenv("ADMIN_TOKEN", "secret-admin")
    monkeypatch.setenv("FREE_JOBS_PER_HOUR", "50")
    monkeypatch.setenv("FREE_JOBS_PER_DAY", "50")
    monkeypatch.setenv("TRUST_PROXY", "1")
    from app import config

    config.reload()
    yield config.settings
    config.reload()

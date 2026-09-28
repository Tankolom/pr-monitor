import os

import numpy as np
import pytest
import soundfile as sf

from app.audio import io
from app.audio.analysis import analyze
from app.audio.pipeline import Options, export, process
from app.audio.planner import make_plans
from app.audio.render import SIGNAL_LEAD, render
from conftest import BAR, SR


@pytest.fixture(scope="module")
def song(song_path):
    return io.decode(song_path)


@pytest.fixture(scope="module")
def an(song):
    return analyze(song)


def test_probe_and_decode(song_path, song):
    info = io.probe(song_path)
    assert abs(info["duration"] - len(song) / SR) < 0.05
    assert song.shape[1] == 2 and song.dtype == np.float32


def test_probe_rejects_garbage(tmp_path):
    p = tmp_path / "x.mp3"
    p.write_bytes(b"not audio at all" * 100)
    with pytest.raises(io.AudioError):
        io.probe(str(p))


def test_analysis_finds_bars(an):
    assert not an.rubato
    assert an.unit == "bar"
    assert an.meter == 4
    assert abs(an.tempo - 120) < 3
    bars = np.diff(an.bounds[:-1])
    assert abs(np.median(bars) - BAR) < 0.05
    # сильные доли стоят на сетке тактов (кратны 2 с)
    phase = (an.bounds[:-1] / BAR) % 1
    phase = np.minimum(phase, 1 - phase)
    assert np.median(phase) < 0.05


@pytest.mark.parametrize("target", [45.0, 60.0, 90.0 - 7.3])
def test_shorten_exact_and_on_bars(song, an, target):
    plans = make_plans(an, target)
    assert plans, "должен быть хотя бы один вариант"
    for p in plans:
        assert abs(p.stretch - 1) <= 0.035 or p.kind == "fade"
        audio, seams = render(song, p, target, with_signal=False, xfade=0.06)
        assert len(audio) == int(round(target * SR))
        for i, j in p.seams:
            for t in (an.bounds[i], an.bounds[j]):
                assert min((t / BAR) % 1, 1 - (t / BAR) % 1) < 0.06, "склейка должна быть на сильной доле"
        assert np.abs(audio).max() <= 1.0


def test_best_shorten_uses_repetition(an):
    """В песне A B A B A лучший стык — между одинаковыми разделами (стоимость низкая)."""
    best = make_plans(an, 50.0)[0]
    assert best.kind == "cut"
    assert max(best.seam_costs) < 0.55


def test_extend(song, an):
    plans = make_plans(an, 150.0)
    assert plans and plans[0].kind in ("extend", "stretch")
    audio, _ = render(song, plans[0], 150.0, with_signal=False, xfade=0.06)
    assert len(audio) == 150 * SR


def test_signal_and_fade(song, an):
    plans = make_plans(an, 40.0, ending="fade")
    assert plans[0].kind == "fade"
    audio, _ = render(song, plans[0], 40.0, with_signal=True, xfade=0.06)
    assert len(audio) == int((40.0 + SIGNAL_LEAD) * SR)
    lead = audio[: int(SIGNAL_LEAD * SR)]
    assert np.abs(lead[: int(0.3 * SR)]).max() > 0.1           # есть «пик»
    assert np.abs(lead[int(0.5 * SR):]).max() < 1e-4           # потом тишина
    assert np.abs(audio[-200:]).max() < 0.02                   # затухание в конце


def test_pipeline_outputs(song_path, tmp_path):
    out = str(tmp_path / "job")
    meta = process(song_path, out, Options(target=60.0, signal=False))
    assert 1 <= len(meta["variants"]) <= 3
    for v in meta["variants"]:
        assert abs(v["duration"] - 60.0) < 1e-3
        assert os.path.exists(os.path.join(out, f"v{v['index']}.flac"))
        assert os.path.exists(os.path.join(out, f"v{v['index']}_preview.mp3"))
        assert len(v["peaks"]) == 600
    mp3 = export(out, 0, "mp3", "Тест")
    wav = export(out, 0, "wav", "Тест")
    assert io.probe(mp3)["duration"] == pytest.approx(60.0, abs=0.08)
    y, sr = sf.read(wav)
    assert sr == SR and abs(len(y) / sr - 60.0) < 1e-3


def test_options_validation():
    with pytest.raises(io.AudioError):
        Options(target=5).validate()
    with pytest.raises(io.AudioError):
        Options(target=60, tempo=1.5).validate()


def test_too_long_extension(song_path, tmp_path):
    with pytest.raises(io.AudioError):
        process(song_path, str(tmp_path / "x"), Options(target=500))

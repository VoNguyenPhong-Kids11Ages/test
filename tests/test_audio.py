import os
import sys
import wave

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt import QiffltError, alphabet  # noqa: E402
from qifflt.audio import render_audio  # noqa: E402


def tag(name: str) -> str:
    return alphabet.encode(name)


def test_single_note_produces_valid_wav(tmp_path):
    out = tmp_path / "note.wav"
    src = f'《{tag("note")} {tag("pitch")}="A4" {tag("dur")}="250"⁄》'
    duration = render_audio(src, str(out))
    assert out.exists()
    assert duration == pytest.approx(0.25, abs=0.01)
    with wave.open(str(out), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 44100
        assert w.getnframes() > 0


def test_freq_attribute_also_works(tmp_path):
    out = tmp_path / "freq.wav"
    src = f'《{tag("note")} {tag("freq")}="440" {tag("dur")}="100"⁄》'
    render_audio(src, str(out))
    assert out.exists()


def test_rest_adds_silence(tmp_path):
    out = tmp_path / "rest.wav"
    src = f'《{tag("rest")} {tag("dur")}="500"⁄》'
    duration = render_audio(src, str(out))
    assert duration == pytest.approx(0.5, abs=0.01)


def test_repeat_multiplies_duration(tmp_path):
    out = tmp_path / "repeat.wav"
    src = (
        f'《{tag("repeat")} {tag("times")}="3"》'
        f'《{tag("note")} {tag("pitch")}="C4" {tag("dur")}="100"⁄》'
        f'《⁄{tag("repeat")}》'
    )
    duration = render_audio(src, str(out))
    assert duration == pytest.approx(0.3, abs=0.01)


def test_speak_sonifies_text(tmp_path):
    out = tmp_path / "speak.wav"
    text = alphabet.encode("hi")
    src = f'《{tag("speak")} {tag("dur")}="100"》「{text}」《⁄{tag("speak")}》'
    duration = render_audio(src, str(out))
    # 2 letters * (100ms tone + 15ms gap) = 230ms
    assert duration == pytest.approx(0.23, abs=0.02)


def test_track_groups_children(tmp_path):
    out = tmp_path / "track.wav"
    src = (
        f'《{tag("track")}》'
        f'《{tag("note")} {tag("pitch")}="C4" {tag("dur")}="100"⁄》'
        f'《{tag("note")} {tag("pitch")}="D4" {tag("dur")}="100"⁄》'
        f'《⁄{tag("track")}》'
    )
    duration = render_audio(src, str(out))
    assert duration == pytest.approx(0.2, abs=0.01)


def test_unknown_tag_is_qifflt_error(tmp_path):
    with pytest.raises(QiffltError) as exc:
        render_audio(f'《{tag("bogus")}⁄》', str(tmp_path / "x.wav"))
    assert "unknown audio tag" in str(exc.value)


def test_invalid_pitch_is_qifflt_error(tmp_path):
    with pytest.raises(QiffltError) as exc:
        render_audio(
            f'《{tag("note")} {tag("pitch")}="Z9"⁄》', str(tmp_path / "x.wav")
        )
    assert "invalid note pitch" in str(exc.value)


def test_note_without_pitch_or_freq_is_error(tmp_path):
    with pytest.raises(QiffltError) as exc:
        render_audio(f'《{tag("note")}⁄》', str(tmp_path / "x.wav"))
    assert "requires a 'pitch' or 'freq'" in str(exc.value)


def test_include_splices_in_another_audio_file(tmp_path):
    (tmp_path / "chime.qfa").write_text(
        f'《{tag("note")} {tag("pitch")}="A4" {tag("dur")}="200"⁄》', encoding="utf-8"
    )
    main_src = f'《{tag("include")} {tag("src")}="chime.qfa"⁄》'
    out = tmp_path / "main.wav"
    duration = render_audio(main_src, str(out), base_dir=str(tmp_path))
    assert duration == pytest.approx(0.2, abs=0.01)

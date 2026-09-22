"""
Qifflt Audio — a hypertext audio markup language, spelled with the same
Qifflt alphabet and the same 《tag》 bracket syntax as Qifflt Markup, but
interpreted as *sound* instead of HTML. It renders to a real, playable
mono 16-bit PCM `.wav` file using nothing but the Python standard
library (`wave`, `math`, `struct`) — no network, no external services.

Recognized tags (names are spelled with Qifflt letter-glyphs, exactly
like in Qifflt Markup — `tag('note')` below is shorthand for "the
letters n-o-t-e written as glyphs"):

    《track》 ... 《⁄track》              a grouping of sound events
    《repeat times="3"》 ... 《⁄repeat》   replay the children N times
    《note pitch="A4" dur="300"⁄》        a tone: scientific pitch name
                                          (C4, D#5, Bb3, ...) or freq="440"
    《rest dur="200"⁄》                   silence, in milliseconds
    《speak dur="150"》text《⁄speak》     *sonification*, not real speech:
                                          each letter of the text is
                                          mapped to a tone on a fixed
                                          two-octave scale, so a phrase
                                          becomes a distinctive, fully
                                          original little melody
    《include src="other.qfa"⁄》          splice in another Qifflt Audio
                                          document (hypertext linking)

`speak` text may be written as plain text or as a 「glyph string」; both
decode to the same tones — this is a *tone sonification* of text, not a
real text-to-speech voice.
"""

from __future__ import annotations

import math
import os
import struct
import wave

from .errors import QiffltError
from .markup import MarkupElement, MarkupText, parse_markup

SAMPLE_RATE = 44100
DEFAULT_NOTE_DUR_MS = 300.0
DEFAULT_SPEAK_LETTER_DUR_MS = 150.0
DEFAULT_AMPLITUDE = 0.5
_FADE_SECONDS = 0.005

_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# `speak` sonification scale: 'a' is middle C, each following letter
# steps up one semitone, spanning a little over two octaves by 'z'.
_MIDDLE_C = 261.6255653005986


def _letter_freq(ch: str) -> float | None:
    lower = ch.lower()
    if "a" <= lower <= "z":
        semitone = ord(lower) - ord("a")
        return _MIDDLE_C * (2.0 ** (semitone / 12.0))
    return None  # non-letters become brief silence


def _pitch_to_freq(pitch: str) -> float:
    pitch = pitch.strip()
    if not pitch:
        raise QiffltError("empty pitch")
    letter = pitch[0].upper()
    if letter not in _SEMITONE:
        raise QiffltError(f"invalid note pitch '{pitch}'")
    semitone = _SEMITONE[letter]
    idx = 1
    if idx < len(pitch) and pitch[idx] in "#b":
        semitone += 1 if pitch[idx] == "#" else -1
        idx += 1
    octave_str = pitch[idx:]
    if not octave_str or not (octave_str.lstrip("-").isdigit()):
        raise QiffltError(f"invalid note pitch '{pitch}': missing octave number")
    octave = int(octave_str)
    midi = 12 * (octave + 1) + semitone
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _duration_ms(attrs: dict, default: float) -> float:
    if "dur" in attrs:
        try:
            return float(attrs["dur"])
        except ValueError:
            raise QiffltError(f"invalid duration '{attrs['dur']}'")
    return default


class _AudioWalker:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._stack: list[str] = []
        self.events: list[tuple[float | None, float]] = []  # (freq_or_None, ms)

    def walk(self, nodes: list) -> None:
        for node in nodes:
            if isinstance(node, MarkupText):
                if node.value.strip():
                    raise QiffltError(
                        "unexpected text outside a 'speak' tag in Qifflt Audio"
                    )
                continue
            self._element(node)

    def _element(self, node: MarkupElement) -> None:
        tag = node.tag
        if tag == "track":
            self.walk(node.children)
        elif tag == "repeat":
            try:
                times = int(node.attrs.get("times", "1"))
            except ValueError:
                raise QiffltError(f"invalid repeat 'times' value '{node.attrs.get('times')}'")
            for _ in range(times):
                self.walk(node.children)
        elif tag == "note":
            if "pitch" in node.attrs:
                freq = _pitch_to_freq(node.attrs["pitch"])
            elif "freq" in node.attrs:
                try:
                    freq = float(node.attrs["freq"])
                except ValueError:
                    raise QiffltError(f"invalid freq '{node.attrs['freq']}'")
            else:
                raise QiffltError("'note' requires a 'pitch' or 'freq' attribute")
            self.events.append((freq, _duration_ms(node.attrs, DEFAULT_NOTE_DUR_MS)))
        elif tag == "rest":
            self.events.append((None, _duration_ms(node.attrs, DEFAULT_NOTE_DUR_MS)))
        elif tag == "speak":
            text = "".join(c.value for c in node.children if isinstance(c, MarkupText))
            letter_dur = _duration_ms(node.attrs, DEFAULT_SPEAK_LETTER_DUR_MS)
            gap_dur = letter_dur * 0.15
            for ch in text:
                freq = _letter_freq(ch)
                self.events.append((freq, letter_dur))
                if gap_dur > 0:
                    self.events.append((None, gap_dur))
        elif tag == "include":
            self._include(node)
        else:
            raise QiffltError(f"unknown audio tag '{tag}'")

    def _include(self, node: MarkupElement) -> None:
        src = node.attrs.get("src") or node.attrs.get("href")
        if not src:
            raise QiffltError("'include' requires a 'src' or 'href' attribute")
        path = src if os.path.isabs(src) else os.path.join(self.base_dir, src)
        path = os.path.normpath(path)
        if path in self._stack:
            raise QiffltError(f"circular include detected: '{src}'")
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as exc:
            raise QiffltError(f"cannot include '{src}': {exc.strerror}")

        nodes = parse_markup(source)
        self._stack.append(path)
        previous_base_dir = self.base_dir
        self.base_dir = os.path.dirname(path) or "."
        try:
            self.walk(nodes)
        finally:
            self.base_dir = previous_base_dir
            self._stack.pop()


def _synthesize_pcm(events: list[tuple[float | None, float]], sample_rate: int) -> bytes:
    fade_n = max(1, int(_FADE_SECONDS * sample_rate))
    out = bytearray()
    for freq, dur_ms in events:
        n = max(1, int(sample_rate * dur_ms / 1000.0))
        if freq is None:
            out.extend(b"\x00\x00" * n)
            continue
        for i in range(n):
            t = i / sample_rate
            value = DEFAULT_AMPLITUDE * math.sin(2 * math.pi * freq * t)
            if i < fade_n:
                value *= i / fade_n
            elif i > n - fade_n:
                value *= max(0.0, (n - i) / fade_n)
            sample = max(-32768, min(32767, int(value * 32767)))
            out += struct.pack("<h", sample)
    return bytes(out)


def render_audio(source: str, out_path: str, base_dir: str | None = None,
                  sample_rate: int = SAMPLE_RATE) -> float:
    """Render a Qifflt Audio document to a mono 16-bit PCM WAV file at
    `out_path`. Returns the resulting duration in seconds."""
    nodes = parse_markup(source)
    walker = _AudioWalker(base_dir or os.getcwd())
    walker.walk(nodes)
    pcm = _synthesize_pcm(walker.events, sample_rate)

    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)

    return len(pcm) / 2 / sample_rate

"""
The Qifflt Alphabet.

Every letter of the Latin alphabet — lowercase and uppercase, kept as
separate glyph sets so case survives round-tripping — has its own,
unique Qifflt glyph. A handful of common punctuation marks and the space
character get glyphs too. This is what lets *any* text — a string
literal, a markup tag name, an attribute, spoken/sung text in an audio
document — be authored entirely "in Qifflt": while coding, every letter
is a Qifflt symbol; once decoded (at parse time, or at render time for
markup/audio), the result is completely ordinary, readable text.

Characters with no entry here (digits, whitespace other than the space
glyph, accented/Vietnamese letters, punctuation not in PUNCT_MAP, other
Unicode text) pass through `encode`/`decode` unchanged, so mixed
plain/cipher content always round-trips safely.
"""

from __future__ import annotations

LOWER = "abcdefghijklmnopqrstuvwxyz"
LOWER_GLYPHS = "☀☁☂☃☄☇☈☉☊☋☌☍☎☏☐☑☒☓☚☛☜☝☞☟☡☤"

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
UPPER_GLYPHS = "♈♉♊♋♌♍♎♏♐♑♒♓♔♕♖♗♘♙♚♛♜♝♞♟♠♡"

assert len(LOWER) == len(LOWER_GLYPHS) == 26
assert len(UPPER) == len(UPPER_GLYPHS) == 26
assert len(set(LOWER_GLYPHS)) == 26
assert len(set(UPPER_GLYPHS)) == 26
assert not (set(LOWER_GLYPHS) & set(UPPER_GLYPHS))

PUNCT = " .,!?'\"-:;()_"
PUNCT_GLYPHS = "‿⁘⁙‼⁉⁗‛⁝⁃⁚⁛⁽⁾"

assert len(PUNCT) == len(PUNCT_GLYPHS)
assert len(set(PUNCT_GLYPHS)) == len(PUNCT_GLYPHS)

# letter/punctuation -> glyph
ENCODE_MAP: dict[str, str] = {}
# glyph -> letter/punctuation
DECODE_MAP: dict[str, str] = {}

for _plain, _glyph in zip(LOWER, LOWER_GLYPHS):
    ENCODE_MAP[_plain] = _glyph
    DECODE_MAP[_glyph] = _plain
for _plain, _glyph in zip(UPPER, UPPER_GLYPHS):
    ENCODE_MAP[_plain] = _glyph
    DECODE_MAP[_glyph] = _plain
for _plain, _glyph in zip(PUNCT, PUNCT_GLYPHS):
    ENCODE_MAP[_plain] = _glyph
    DECODE_MAP[_glyph] = _plain


def encode(text: str) -> str:
    """Turn ordinary text into the Qifflt alphabet. Characters with no
    glyph (digits, Vietnamese diacritics, unmapped punctuation, ...)
    pass through unchanged."""
    return "".join(ENCODE_MAP.get(ch, ch) for ch in text)


def decode(cipher: str) -> str:
    """Turn Qifflt-glyph text back into ordinary text. Characters that
    are not Qifflt glyphs (already-plain letters, digits, spaces, ...)
    pass through unchanged, so glyph and plain text may be freely
    mixed in the same literal."""
    return "".join(DECODE_MAP.get(ch, ch) for ch in cipher)


def is_glyph(ch: str) -> bool:
    return ch in DECODE_MAP


def decode_tag_name(cipher: str) -> str:
    """Decode a markup/audio tag or attribute name. Same as `decode`,
    but also lower-cases the result, since tag/attribute names in the
    rendered output are conventionally lowercase regardless of which
    case of glyph was used to spell them."""
    return decode(cipher).lower()

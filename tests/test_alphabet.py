import os
import string
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt import alphabet as A  # noqa: E402


def test_full_latin_alphabet_has_glyphs():
    for ch in string.ascii_lowercase + string.ascii_uppercase:
        assert ch in A.ENCODE_MAP


def test_roundtrip_plain_sentence():
    text = "Hello, world! Qifflt is fun."
    assert A.decode(A.encode(text)) == text


def test_case_is_preserved():
    assert A.decode(A.encode("Hi")) == "Hi"
    assert A.decode(A.encode("hi")) == "hi"
    assert A.encode("Hi") != A.encode("hi")


def test_unmapped_characters_pass_through():
    text = "abc123 đường"
    encoded = A.encode(text)
    assert "1" in encoded and "2" in encoded and "3" in encoded
    assert A.decode(encoded) == text


def test_lower_and_upper_glyph_sets_disjoint():
    assert not (set(A.LOWER_GLYPHS) & set(A.UPPER_GLYPHS))


def test_all_glyphs_unique():
    all_glyphs = list(A.LOWER_GLYPHS) + list(A.UPPER_GLYPHS) + list(A.PUNCT_GLYPHS)
    assert len(all_glyphs) == len(set(all_glyphs))


def test_decode_tag_name_lowercases():
    assert A.decode_tag_name(A.encode("DIV")) == "div"
    assert A.decode_tag_name(A.encode("div")) == "div"

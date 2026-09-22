import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt import Interpreter, QiffltError, alphabet, parse  # noqa: E402


def run(code: str):
    outputs = []
    Interpreter(output_fn=outputs.append).run(parse(code))
    return outputs


def test_glyph_string_decodes_to_plain_output():
    cipher = alphabet.encode("Hello world")
    out = run(f"₫1¥£!(「{cipher}」)")
    assert out == ["Hello world"]


def test_glyph_string_equals_normal_string():
    cipher = alphabet.encode("same text")
    out_glyph = run(f'₫1¥£!(「{cipher}」)')
    out_plain = run('₫1¥£!("same text")')
    assert out_glyph == out_plain


def test_glyph_string_as_variable_value():
    cipher = alphabet.encode("stored")
    out = run(f"""
1†Φ2 msg 「{cipher}」
₫1¥£!(msg)
""")
    assert out == ["stored"]


def test_glyph_string_can_mix_plain_and_glyph_chars():
    mixed = "H" + alphabet.encode("ello") + " 123"
    out = run(f"₫1¥£!(「{mixed}」)")
    assert out == ["Hello 123"]


def test_unterminated_glyph_string_is_qifflt_error():
    with pytest.raises(QiffltError) as exc:
        run("₫1¥£!(「unterminated")
    assert "unterminated glyph string" in str(exc.value)

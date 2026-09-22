import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt.highlighter import highlight  # noqa: E402

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip(s: str) -> str:
    return _ANSI_RE.sub("", s)


def test_stripping_ansi_reproduces_original_source():
    src = '# comment\n1†Φ2 x 10\n₫1¥£!("hi", x)\n'
    assert _strip(highlight(src)) == src


def test_no_color_returns_source_unchanged():
    src = '₫1¥£!("hi")'
    assert highlight(src, use_color=False) == src


def test_keywords_are_colored():
    out = highlight("1†Φ2 x 10")
    assert "\x1b[" in out


def test_comment_is_colored():
    out = highlight("# a comment\n")
    assert "\x1b[" in out
    assert "# a comment" in _strip(out)


def test_survives_lexer_error_without_raising():
    # '@' is not a valid Qifflt character; highlighting must not crash.
    out = highlight("1†Φ2 x @")
    assert "@" in _strip(out)

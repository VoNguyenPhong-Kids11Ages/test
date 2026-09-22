"""
Optional Pygments lexer for Qifflt, so editors, static-site generators,
and doc tools that already speak Pygments (Sphinx, mkdocs, etc.) get
real syntax highlighting for `.qft` / `.qfx` / `.qfa` files.

This module only does anything if `pygments` is installed — it is an
optional extra (`pip install qifflt[highlight]`), never a hard
dependency of the core language. If Pygments is not installed,
importing this module raises ImportError, same as any other optional
integration; the rest of Qifflt does not import it.
"""

from __future__ import annotations

import re

from pygments.lexer import RegexLexer
from pygments.token import (
    Comment, Keyword, Name, Number, Operator, Punctuation, String, Text,
)

from .lexer import SYMBOL_KEYWORDS, WORD_KEYWORDS, TT

_KEYWORD_TOKENS = {
    TT.SET, TT.IF, TT.ELSE, TT.END, TT.WHILE, TT.FUNC, TT.RETURN,
    TT.AND, TT.OR, TT.NOT, TT.IMPORT,
}
_BUILTIN_TOKENS = {TT.SHOW, TT.INPUT}
_LITERAL_TOKENS = {TT.TRUE, TT.FALSE, TT.NULL}


def _alternation(strings) -> str:
    # Longest first, so multi-glyph symbols aren't shadowed by a prefix.
    return "|".join(re.escape(s) for s in sorted(strings, key=len, reverse=True))


_KEYWORD_SYMS = _alternation(s for s, t in SYMBOL_KEYWORDS.items() if t in _KEYWORD_TOKENS)
_KEYWORD_WORDS = _alternation(w for w, t in WORD_KEYWORDS.items() if t in _KEYWORD_TOKENS)
_BUILTIN_SYMS = _alternation(s for s, t in SYMBOL_KEYWORDS.items() if t in _BUILTIN_TOKENS)
_BUILTIN_WORDS = _alternation(w for w, t in WORD_KEYWORDS.items() if t in _BUILTIN_TOKENS)
_LITERAL_SYMS = _alternation(s for s, t in SYMBOL_KEYWORDS.items() if t in _LITERAL_TOKENS)
_LITERAL_WORDS = _alternation(w for w, t in WORD_KEYWORDS.items() if t in _LITERAL_TOKENS)


class QiffltLexer(RegexLexer):
    """Pygments lexer for Qifflt (`.qft`), Qifflt Markup (`.qfx`), and
    Qifflt Audio (`.qfa`) source."""

    name = "Qifflt"
    aliases = ["qifflt"]
    filenames = ["*.qft", "*.qfx", "*.qfa"]
    mimetypes = ["text/x-qifflt"]

    tokens = {
        "root": [
            (r"#.*$", Comment.Single),
            (r"\s+", Text),
            (r'"(\\.|[^"\\])*"', String.Double),
            (r"「[^」]*」", String.Other),  # Qifflt glyph string literal
            (r"《!--.*?--》", Comment.Multiline),
            (r"《⁄?", Punctuation),  # markup/audio tag delimiters
            (r"⁄?》", Punctuation),
            (_KEYWORD_SYMS, Keyword),
            (_KEYWORD_WORDS, Keyword),
            (_BUILTIN_SYMS, Name.Builtin),
            (_BUILTIN_WORDS, Name.Builtin),
            (_LITERAL_SYMS, Keyword.Constant),
            (_LITERAL_WORDS, Keyword.Constant),
            (r"\d+\.\d+|\d+", Number),
            (r"==|!=|<=|>=|[+\-*/%=<>]", Operator),
            (r"[()\[\],]", Punctuation),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name.Variable),
            # Any remaining Qifflt-alphabet glyph (used bare in markup/
            # audio tag and attribute names outside of 「 」).
            (r"[^\sA-Za-z0-9_#\"()\[\],+\-*/%=<>]", Name.Tag),
        ],
    }

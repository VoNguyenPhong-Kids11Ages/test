#!/usr/bin/env python3
"""
Generate editors/vscode/syntaxes/qifflt.tmLanguage.json directly from
qifflt.lexer's SYMBOL_KEYWORDS / WORD_KEYWORDS tables, so the VS Code
grammar can never drift out of sync with what the language actually
accepts. Run this after changing any keyword alias:

    python3 tools/generate_vscode_grammar.py
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt.lexer import SYMBOL_KEYWORDS, WORD_KEYWORDS, TT  # noqa: E402

KEYWORD_TOKENS = {
    TT.SET, TT.IF, TT.ELSE, TT.END, TT.WHILE, TT.FUNC, TT.RETURN,
    TT.AND, TT.OR, TT.NOT, TT.IMPORT,
}
BUILTIN_TOKENS = {TT.SHOW, TT.INPUT}
LITERAL_TOKENS = {TT.TRUE, TT.FALSE, TT.NULL}


def alternation(strings) -> str:
    # Longest first, so multi-glyph symbols aren't shadowed by a prefix.
    return "|".join(re.escape(s) for s in sorted(strings, key=len, reverse=True))


def build_grammar() -> dict:
    kw_syms = alternation(s for s, t in SYMBOL_KEYWORDS.items() if t in KEYWORD_TOKENS)
    kw_words = alternation(w for w, t in WORD_KEYWORDS.items() if t in KEYWORD_TOKENS)
    bi_syms = alternation(s for s, t in SYMBOL_KEYWORDS.items() if t in BUILTIN_TOKENS)
    bi_words = alternation(w for w, t in WORD_KEYWORDS.items() if t in BUILTIN_TOKENS)
    lit_syms = alternation(s for s, t in SYMBOL_KEYWORDS.items() if t in LITERAL_TOKENS)
    lit_words = alternation(w for w, t in WORD_KEYWORDS.items() if t in LITERAL_TOKENS)

    return {
        "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
        "name": "Qifflt",
        "scopeName": "source.qifflt",
        "fileTypes": ["qft", "qfx", "qfa"],
        "patterns": [
            {"include": "#comments"},
            {"include": "#markup-tags"},
            {"include": "#strings"},
            {"include": "#glyph-strings"},
            {"include": "#numbers"},
            {"include": "#keywords"},
            {"include": "#builtins"},
            {"include": "#literals"},
            {"include": "#operators"},
            {"include": "#punctuation"},
        ],
        "repository": {
            "comments": {
                "patterns": [
                    {"name": "comment.line.number-sign.qifflt", "match": "#.*$"},
                    {"name": "comment.block.qifflt", "begin": "《!--", "end": "--》"},
                ]
            },
            "strings": {
                "name": "string.quoted.double.qifflt",
                "begin": "\"",
                "end": "\"",
                "patterns": [{"name": "constant.character.escape.qifflt", "match": r"\\."}],
            },
            "glyph-strings": {
                "name": "string.other.glyph.qifflt",
                "begin": "「",
                "end": "」",
                "comment": "Text spelled in the Qifflt alphabet; decodes to plain text at parse time.",
            },
            "numbers": {"name": "constant.numeric.qifflt", "match": r"\b\d+(\.\d+)?\b"},
            "keywords": {
                "name": "keyword.control.qifflt",
                "match": f"({kw_syms}|\\b({kw_words})\\b)",
            },
            "builtins": {
                "name": "support.function.builtin.qifflt",
                "match": f"({bi_syms}|\\b({bi_words})\\b)",
            },
            "literals": {
                "name": "constant.language.qifflt",
                "match": f"({lit_syms}|\\b({lit_words})\\b)",
            },
            "operators": {
                "name": "keyword.operator.qifflt",
                "match": r"==|!=|<=|>=|[+\-*/%=<>]",
            },
            "punctuation": {"name": "punctuation.qifflt", "match": r"[()\[\],]"},
            "markup-tags": {
                "patterns": [
                    {"name": "entity.name.tag.qifflt", "match": "《⁄?"},
                    {"name": "entity.name.tag.qifflt", "match": "⁄?》"},
                ]
            },
        },
    }


def main() -> None:
    grammar = build_grammar()
    out_path = os.path.join(
        os.path.dirname(__file__), "..", "editors", "vscode", "syntaxes", "qifflt.tmLanguage.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(grammar, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()

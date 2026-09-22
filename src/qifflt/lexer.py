"""
Qifflt lexer.

Qifflt has no plain-English keywords. Every keyword exists only as one of
two aliases:

  * a SYMBOL alias, built from Unicode currency / math glyphs
  * a WORD alias, an intentionally meaningless lowercase string

Both aliases for a given keyword produce the exact same token type, so the
parser and interpreter never need to know which spelling was used.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from . import alphabet
from .errors import QiffltError


class TT(Enum):
    # literals
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()

    # keywords (each has a SYMBOL alias and a WORD alias, see tables below)
    SHOW = auto()
    SET = auto()
    IF = auto()
    ELSE = auto()
    END = auto()
    WHILE = auto()
    FUNC = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    INPUT = auto()
    IMPORT = auto()

    # operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()      # '=' (reserved for future use; SET is the real assignment stmt)
    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()

    # punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()

    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TT
    value: object
    line: int

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


# ---------------------------------------------------------------------------
# Keyword alias tables
# ---------------------------------------------------------------------------
# SYMBOL aliases: sequences of Unicode currency / math glyphs. Matched by
# longest-match at the lexer's current position so that keywords sharing a
# leading glyph (e.g. the leading "1" of SET and IF) are never confused.
SYMBOL_KEYWORDS: dict[str, TT] = {
    "₫1¥£!": TT.SHOW,
    "1†Φ2": TT.SET,
    "1₽53": TT.IF,
    "Ω¥0¢": TT.ELSE,
    "±•₹£": TT.END,
    "•₽÷•": TT.WHILE,
    "5√£Ω": TT.FUNC,
    "€97¥": TT.RETURN,
    "±±₹§": TT.TRUE,
    "¶50£": TT.FALSE,
    "₹∆0±": TT.NULL,
    "±†√Φ": TT.AND,
    "8Ψ£¥": TT.OR,
    "30√Ω": TT.NOT,
    "∞2₩7": TT.INPUT,
    "₫+€×■@": TT.IMPORT,
}
# Longest symbols first, so a shorter symbol that happens to be a prefix of
# a longer one never wins by accident.
_SYMBOLS_BY_LENGTH = sorted(SYMBOL_KEYWORDS.keys(), key=len, reverse=True)

# WORD aliases: meaningless lowercase strings, matched only as a *whole*
# identifier (never as a prefix of a longer identifier).
WORD_KEYWORDS: dict[str, TT] = {
    "fpjrsidnvt": TT.SHOW,
    "uzljmwgyv": TT.SET,
    "cqwvlmmzx": TT.IF,
    "ohfzkvwto": TT.ELSE,
    "cnutbvaug": TT.END,
    "oxzskaztk": TT.WHILE,
    "gtfqqqfyv": TT.FUNC,
    "zqpryuxlx": TT.RETURN,
    "bfkcgorib": TT.TRUE,
    "njxebuolm": TT.FALSE,
    "wggepmtnr": TT.NULL,
    "mtgzytnfw": TT.AND,
    "rtgunjyrk": TT.OR,
    "osmumetiy": TT.NOT,
    "wakcipqtm": TT.INPUT,
    "vhqzomntyk": TT.IMPORT,
}

_TWO_CHAR_OPS = {
    "==": TT.EQEQ,
    "!=": TT.NEQ,
    "<=": TT.LE,
    ">=": TT.GE,
}
_ONE_CHAR_OPS = {
    "+": TT.PLUS,
    "-": TT.MINUS,
    "*": TT.STAR,
    "/": TT.SLASH,
    "%": TT.PERCENT,
    "=": TT.ASSIGN,
    "<": TT.LT,
    ">": TT.GT,
}
_PUNCT = {
    "(": TT.LPAREN,
    ")": TT.RPAREN,
    "[": TT.LBRACKET,
    "]": TT.RBRACKET,
    ",": TT.COMMA,
}


def _is_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch == "_"


def _is_ident_continue(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.length = len(source)

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < self.length else ""

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while True:
            tok = self._next_token()
            tokens.append(tok)
            if tok.type == TT.EOF:
                break
        return tokens

    def _next_token(self) -> Token:
        self._skip_ignorable()

        if self.pos >= self.length:
            return Token(TT.EOF, None, self.line)

        ch = self.src[self.pos]

        if ch == "\n":
            line = self.line
            self.pos += 1
            self.line += 1
            return Token(TT.NEWLINE, "\n", line)

        # Longest-match symbol keywords first.
        for sym in _SYMBOLS_BY_LENGTH:
            if self.src.startswith(sym, self.pos):
                tok = Token(SYMBOL_KEYWORDS[sym], sym, self.line)
                self.pos += len(sym)
                return tok

        if ch.isdigit():
            return self._read_number()

        if ch == '"':
            return self._read_string()

        if ch == "「":
            return self._read_glyph_string()

        if _is_ident_start(ch):
            return self._read_ident_or_word_keyword()

        two = self.src[self.pos:self.pos + 2]
        if two in _TWO_CHAR_OPS:
            tok = Token(_TWO_CHAR_OPS[two], two, self.line)
            self.pos += 2
            return tok

        if ch in _ONE_CHAR_OPS:
            tok = Token(_ONE_CHAR_OPS[ch], ch, self.line)
            self.pos += 1
            return tok

        if ch in _PUNCT:
            tok = Token(_PUNCT[ch], ch, self.line)
            self.pos += 1
            return tok

        raise QiffltError(f"unexpected character {ch!r}", self.line)

    def _skip_ignorable(self) -> None:
        while self.pos < self.length:
            ch = self.src[self.pos]
            if ch == "#":
                while self.pos < self.length and self.src[self.pos] != "\n":
                    self.pos += 1
            elif ch in " \t\r":
                self.pos += 1
            else:
                break

    def _read_number(self) -> Token:
        start = self.pos
        line = self.line
        is_float = False
        while self.pos < self.length and self.src[self.pos].isdigit():
            self.pos += 1
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self.pos += 1
            while self.pos < self.length and self.src[self.pos].isdigit():
                self.pos += 1
        text = self.src[start:self.pos]
        value = float(text) if is_float else int(text)
        return Token(TT.NUMBER, value, line)

    def _read_string(self) -> Token:
        line = self.line
        self.pos += 1  # skip opening quote
        chars: list[str] = []
        while True:
            if self.pos >= self.length:
                raise QiffltError("unterminated string", line)
            ch = self.src[self.pos]
            if ch == '"':
                self.pos += 1
                break
            if ch == "\n":
                raise QiffltError("unterminated string", line)
            if ch == "\\":
                self.pos += 1
                if self.pos >= self.length:
                    raise QiffltError("unterminated string", line)
                esc = self.src[self.pos]
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                chars.append(mapping.get(esc, esc))
                self.pos += 1
            else:
                chars.append(ch)
                self.pos += 1
        return Token(TT.STRING, "".join(chars), line)

    def _read_glyph_string(self) -> Token:
        """Read a 「...」 literal: text written entirely (or partly) in
        the Qifflt alphabet. Decoded to plain text right here at lex
        time, so it becomes an ordinary STRING token — the rest of the
        pipeline never knows the source was written in glyphs. Unlike
        `"..."` strings, glyph strings may span multiple lines, since
        they are meant for prose/hypertext-style content."""
        line = self.line
        self.pos += 1  # skip opening 「
        start = self.pos
        while True:
            if self.pos >= self.length:
                raise QiffltError("unterminated glyph string", line)
            ch = self.src[self.pos]
            if ch == "」":
                raw = self.src[start:self.pos]
                self.pos += 1
                return Token(TT.STRING, alphabet.decode(raw), line)
            if ch == "\n":
                self.line += 1
            self.pos += 1

    def _read_ident_or_word_keyword(self) -> Token:
        start = self.pos
        line = self.line
        while self.pos < self.length and _is_ident_continue(self.src[self.pos]):
            self.pos += 1
        text = self.src[start:self.pos]
        if text in WORD_KEYWORDS:
            return Token(WORD_KEYWORDS[text], text, line)
        return Token(TT.IDENT, text, line)


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()

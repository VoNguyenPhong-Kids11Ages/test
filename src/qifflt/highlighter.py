"""
ANSI terminal syntax highlighting for Qifflt source, driven by the same
lexer the interpreter uses (so highlighting can never drift out of sync
with what the language actually accepts).
"""

from __future__ import annotations

from .errors import QiffltError
from .lexer import TT, Lexer

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
ITALIC = "\x1b[3m"
UNDERLINE = "\x1b[4m"

# 256-color-safe ANSI codes, chosen for readability on both light and
# dark terminal themes.
COLORS = {
    "keyword": "\x1b[38;5;170m",   # magenta  - control-flow / declaration keywords
    "builtin": "\x1b[38;5;110m",   # blue     - show / input
    "literal": "\x1b[38;5;215m",   # orange   - true / false / null
    "string": "\x1b[38;5;114m",    # green    - "..." and 「...」 strings
    "number": "\x1b[38;5;180m",    # tan      - numeric literals
    "operator": "\x1b[38;5;203m",  # red      - + - * / etc.
    "punct": "\x1b[38;5;245m",     # gray     - ( ) [ ] ,
    "ident": "",                    # default terminal color
    "comment": DIM + ITALIC,
}

_KEYWORD_TYPES = {
    TT.SET, TT.IF, TT.ELSE, TT.END, TT.WHILE, TT.FUNC, TT.RETURN,
    TT.AND, TT.OR, TT.NOT, TT.IMPORT,
}
_BUILTIN_TYPES = {TT.SHOW, TT.INPUT}
_LITERAL_TYPES = {TT.TRUE, TT.FALSE, TT.NULL}
_OPERATOR_TYPES = {
    TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH, TT.PERCENT, TT.ASSIGN,
    TT.EQEQ, TT.NEQ, TT.LT, TT.GT, TT.LE, TT.GE,
}
_PUNCT_TYPES = {TT.LPAREN, TT.RPAREN, TT.LBRACKET, TT.RBRACKET, TT.COMMA}


def _category(tok_type: TT) -> str:
    if tok_type in _KEYWORD_TYPES:
        return "keyword"
    if tok_type in _BUILTIN_TYPES:
        return "builtin"
    if tok_type in _LITERAL_TYPES:
        return "literal"
    if tok_type == TT.STRING:
        return "string"
    if tok_type == TT.NUMBER:
        return "number"
    if tok_type in _OPERATOR_TYPES:
        return "operator"
    if tok_type in _PUNCT_TYPES:
        return "punct"
    return "ident"


def highlight(source: str, use_color: bool = True) -> str:
    """Return `source` with ANSI color codes wrapped around each token.
    Comments are colored distinctly; whitespace is preserved exactly.
    On a lexer error, everything from that point on is emitted as-is
    (uncolored) rather than raising."""
    if not use_color:
        return source

    lexer = Lexer(source)
    out: list[str] = []

    while True:
        # Manually mirror Lexer._skip_ignorable's whitespace/comment
        # skipping so we can color comments distinctly, then hand off
        # to the real lexer (which will find nothing left to skip).
        gap_start = lexer.pos
        while lexer.pos < lexer.length and lexer.src[lexer.pos] in " \t\r":
            lexer.pos += 1
        if lexer.pos < lexer.length and lexer.src[lexer.pos] == "#":
            comment_start = lexer.pos
            while lexer.pos < lexer.length and lexer.src[lexer.pos] != "\n":
                lexer.pos += 1
            out.append(source[gap_start:comment_start])
            out.append(f"{COLORS['comment']}{source[comment_start:lexer.pos]}{RESET}")
        else:
            out.append(source[gap_start:lexer.pos])

        pre_pos = lexer.pos
        try:
            tok = lexer._next_token()  # noqa: SLF001 - intentional, same module family
        except QiffltError:
            out.append(source[pre_pos:])
            break

        token_text = source[pre_pos:lexer.pos]
        if tok.type == TT.EOF:
            break
        color = COLORS.get(_category(tok.type), "")
        out.append(f"{color}{token_text}{RESET}" if color else token_text)

    return "".join(out)

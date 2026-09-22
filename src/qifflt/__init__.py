"""Qifflt: an intentionally unreadable little programming, markup, and
audio language, all built on one shared alphabet."""

from . import alphabet
from .errors import QiffltError
from .interpreter import Interpreter, QiffltFunction
from .qparser import parse
from .lexer import tokenize

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "QiffltError",
    "Interpreter",
    "QiffltFunction",
    "parse",
    "tokenize",
    "alphabet",
]

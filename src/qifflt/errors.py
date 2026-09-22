"""
Qifflt error types.

Every error that can be attributed to a Qifflt program (as opposed to a bug
in the implementation itself) is raised as a QiffltError so the CLI can
print a single clean line instead of a raw Python traceback.
"""

from __future__ import annotations


class QiffltError(Exception):
    """A user-facing Qifflt error: lexing, parsing, or runtime."""

    def __init__(self, message: str, line: int | None = None):
        self.message = message
        self.line = line
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.line is not None:
            return f"Qifflt error (line {self.line}): {self.message}"
        return f"Qifflt error: {self.message}"


class QiffltReturn(Exception):
    """Internal control-flow signal used to unwind a function call on
    return. Never surfaces to the user; the interpreter always catches it
    at the function-call boundary."""

    def __init__(self, value):
        self.value = value
        super().__init__("return")

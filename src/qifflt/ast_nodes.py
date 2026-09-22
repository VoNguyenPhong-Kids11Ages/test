"""
Qifflt AST node definitions.

Plain dataclasses; the parser builds these, the interpreter walks them.
Every node carries the source line it started on, for error reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    line: int


# ---- expressions ----------------------------------------------------------

@dataclass
class NumberLit(Node):
    value: float | int


@dataclass
class StringLit(Node):
    value: str


@dataclass
class BoolLit(Node):
    value: bool


@dataclass
class NullLit(Node):
    pass


@dataclass
class ListLit(Node):
    items: list[Node]


@dataclass
class Identifier(Node):
    name: str


@dataclass
class Builtin(Node):
    """Reference to a builtin keyword usable as a call target: show / input."""
    name: str  # "show" or "input"


@dataclass
class UnaryOp(Node):
    op: str
    operand: Node


@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Call(Node):
    callee: Node
    args: list[Node]


@dataclass
class Index(Node):
    target: Node
    index: Node


# ---- statements -------------------------------------------------------------

@dataclass
class Program(Node):
    statements: list[Node]


@dataclass
class ExprStmt(Node):
    expr: Node


@dataclass
class SetStmt(Node):
    name: str
    value: Node


@dataclass
class IfStmt(Node):
    condition: Node
    then_body: list[Node]
    else_body: list[Node] = field(default_factory=list)


@dataclass
class WhileStmt(Node):
    condition: Node
    body: list[Node]


@dataclass
class FuncDef(Node):
    name: str
    params: list[str]
    body: list[Node]


@dataclass
class ReturnStmt(Node):
    value: Node | None


@dataclass
class ImportStmt(Node):
    path: str

"""
Qifflt interpreter: a straightforward tree-walking evaluator.

Runtime value mapping:
    Qifflt number   -> Python int / float
    Qifflt string   -> Python str
    Qifflt boolean  -> Python bool
    Qifflt null     -> Python None
    Qifflt list     -> Python list
    Qifflt function -> QiffltFunction
"""

from __future__ import annotations

import os

from . import ast_nodes as A
from .errors import QiffltError, QiffltReturn
from .qparser import parse


class Environment:
    """A single lexical scope, chained to its parent for closures."""

    __slots__ = ("vars", "parent")

    def __init__(self, parent: "Environment | None" = None):
        self.vars: dict[str, object] = {}
        self.parent = parent

    def get(self, name: str, line: int):
        env: Environment | None = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise QiffltError(f"undefined variable '{name}'", line)

    def set(self, name: str, value: object) -> None:
        """Assign in the nearest enclosing scope that already defines the
        name, otherwise create it in the current scope. This gives `set`
        Python-like "define-or-update" semantics."""
        env: Environment | None = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        self.vars[name] = value

    def define_here(self, name: str, value: object) -> None:
        self.vars[name] = value


class QiffltFunction:
    """A user-defined Qifflt function: parameters, body, and the
    environment it closes over."""

    def __init__(self, name: str, params: list[str], body: list[A.Node],
                 closure: Environment):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<function {self.name}/{len(self.params)}>"


def _truthy(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, list):
        return len(value) > 0
    return True


def _stringify(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, list):
        return "[" + ", ".join(_stringify(v) for v in value) + "]"
    return str(value)


class Interpreter:
    def __init__(self, base_dir: str | None = None, input_fn=input, output_fn=print):
        self.globals = Environment()
        self.base_dir = base_dir or os.getcwd()
        self._input_fn = input_fn
        self._output_fn = output_fn
        # Absolute paths already imported, so a module is only ever
        # executed once even if imported from multiple places.
        self._imported: set[str] = set()

    # -- public API ---------------------------------------------------------

    def run(self, program: A.Program) -> None:
        self._exec_block(program.statements, self.globals)

    def run_source(self, source: str) -> None:
        self.run(parse(source))

    # -- statement execution --------------------------------------------------

    def _exec_block(self, statements: list[A.Node], env: Environment) -> None:
        for stmt in statements:
            self._exec(stmt, env)

    def _exec(self, node: A.Node, env: Environment) -> None:
        method = getattr(self, f"_exec_{type(node).__name__}", None)
        if method is None:  # pragma: no cover - defensive
            raise QiffltError(f"cannot execute {type(node).__name__}", node.line)
        method(node, env)

    def _exec_ExprStmt(self, node: A.ExprStmt, env: Environment) -> None:
        self._eval(node.expr, env)

    def _exec_SetStmt(self, node: A.SetStmt, env: Environment) -> None:
        value = self._eval(node.value, env)
        env.set(node.name, value)

    def _exec_IfStmt(self, node: A.IfStmt, env: Environment) -> None:
        if _truthy(self._eval(node.condition, env)):
            self._exec_block(node.then_body, env)
        else:
            self._exec_block(node.else_body, env)

    def _exec_WhileStmt(self, node: A.WhileStmt, env: Environment) -> None:
        while _truthy(self._eval(node.condition, env)):
            self._exec_block(node.body, env)

    def _exec_FuncDef(self, node: A.FuncDef, env: Environment) -> None:
        fn = QiffltFunction(node.name, node.params, node.body, env)
        env.define_here(node.name, fn)

    def _exec_ReturnStmt(self, node: A.ReturnStmt, env: Environment) -> None:
        value = self._eval(node.value, env) if node.value is not None else None
        raise QiffltReturn(value)

    def _exec_ImportStmt(self, node: A.ImportStmt, env: Environment) -> None:
        path = node.path
        if not os.path.isabs(path):
            path = os.path.join(self.base_dir, path)
        path = os.path.normpath(path)

        if path in self._imported:
            return  # already loaded: importing twice is a no-op

        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as exc:
            raise QiffltError(f"cannot import '{node.path}': {exc.strerror}", node.line)

        self._imported.add(path)

        module_env = Environment(parent=None)
        previous_base_dir = self.base_dir
        self.base_dir = os.path.dirname(path) or "."
        try:
            program = parse(source)
            self._exec_block(program.statements, module_env)
        finally:
            self.base_dir = previous_base_dir

        # Merge every top-level binding from the module into the importing
        # scope (import behaves like "bring everything in").
        for name, value in module_env.vars.items():
            env.define_here(name, value)

    # -- expression evaluation ------------------------------------------------

    def _eval(self, node: A.Node, env: Environment):
        method = getattr(self, f"_eval_{type(node).__name__}", None)
        if method is None:  # pragma: no cover - defensive
            raise QiffltError(f"cannot evaluate {type(node).__name__}", node.line)
        return method(node, env)

    def _eval_NumberLit(self, node: A.NumberLit, env: Environment):
        return node.value

    def _eval_StringLit(self, node: A.StringLit, env: Environment):
        return node.value

    def _eval_BoolLit(self, node: A.BoolLit, env: Environment):
        return node.value

    def _eval_NullLit(self, node: A.NullLit, env: Environment):
        return None

    def _eval_ListLit(self, node: A.ListLit, env: Environment):
        return [self._eval(item, env) for item in node.items]

    def _eval_Identifier(self, node: A.Identifier, env: Environment):
        return env.get(node.name, node.line)

    def _eval_Builtin(self, node: A.Builtin, env: Environment):
        return node.name  # resolved specially in _eval_Call

    def _eval_UnaryOp(self, node: A.UnaryOp, env: Environment):
        value = self._eval(node.operand, env)
        if node.op == "-":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise QiffltError("unknown operator: '-' on non-number", node.line)
            return -value
        if node.op == "not":
            return not _truthy(value)
        raise QiffltError(f"unknown operator '{node.op}'", node.line)  # pragma: no cover

    def _eval_BinaryOp(self, node: A.BinaryOp, env: Environment):
        op = node.op

        if op == "and":
            left = self._eval(node.left, env)
            if not _truthy(left):
                return left
            return self._eval(node.right, env)
        if op == "or":
            left = self._eval(node.left, env)
            if _truthy(left):
                return left
            return self._eval(node.right, env)

        left = self._eval(node.left, env)
        right = self._eval(node.right, env)

        if op == "==":
            return left == right
        if op == "!=":
            return left != right

        if op in ("<", ">", "<=", ">="):
            if not (self._is_number(left) and self._is_number(right)) and not (
                isinstance(left, str) and isinstance(right, str)
            ):
                raise QiffltError(
                    f"unknown operator: '{op}' between incompatible types", node.line
                )
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            return left >= right

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise QiffltError("unknown operator: '+' between incompatible types", node.line)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if self._is_number(left) and self._is_number(right):
                return left + right
            raise QiffltError("unknown operator: '+' between incompatible types", node.line)

        if op in ("-", "*", "/", "%"):
            if not (self._is_number(left) and self._is_number(right)):
                raise QiffltError(
                    f"unknown operator: '{op}' between incompatible types", node.line
                )
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise QiffltError("division by zero", node.line)
                result = left / right
                if isinstance(left, int) and isinstance(right, int) and left % right == 0:
                    return left // right
                return result
            if op == "%":
                if right == 0:
                    raise QiffltError("division by zero", node.line)
                return left % right

        raise QiffltError(f"unknown operator '{op}'", node.line)  # pragma: no cover

    @staticmethod
    def _is_number(value) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _eval_Index(self, node: A.Index, env: Environment):
        target = self._eval(node.target, env)
        index = self._eval(node.index, env)
        if not isinstance(target, (list, str)):
            raise QiffltError("invalid indexing: target is not a list or string", node.line)
        if not isinstance(index, int) or isinstance(index, bool):
            raise QiffltError("invalid indexing: index must be an integer", node.line)
        if index < 0 or index >= len(target):
            raise QiffltError(f"invalid indexing: index {index} out of range", node.line)
        return target[index]

    def _eval_Call(self, node: A.Call, env: Environment):
        if isinstance(node.callee, A.Builtin):
            return self._call_builtin(node.callee.name, node.args, env, node.line)

        callee = self._eval(node.callee, env)
        args = [self._eval(a, env) for a in node.args]

        if isinstance(callee, QiffltFunction):
            return self._call_function(callee, args, node.line)

        raise QiffltError("invalid function call: target is not callable", node.line)

    def _call_builtin(self, name: str, arg_nodes: list[A.Node], env: Environment, line: int):
        args = [self._eval(a, env) for a in arg_nodes]
        if name == "show":
            self._output_fn(" ".join(_stringify(a) for a in args))
            return None
        if name == "input":
            if len(args) > 1:
                raise QiffltError("wrong argument count: input expects 0 or 1 argument", line)
            prompt = _stringify(args[0]) if args else ""
            return str(self._input_fn(prompt))
        raise QiffltError(f"invalid function call: unknown builtin '{name}'", line)  # pragma: no cover

    def _call_function(self, fn: QiffltFunction, args: list, line: int):
        if len(args) != len(fn.params):
            raise QiffltError(
                f"wrong argument count: '{fn.name}' expects {len(fn.params)}, got {len(args)}",
                line,
            )
        call_env = Environment(parent=fn.closure)
        for param, value in zip(fn.params, args):
            call_env.define_here(param, value)
        try:
            self._exec_block(fn.body, call_env)
        except QiffltReturn as ret:
            return ret.value
        return None

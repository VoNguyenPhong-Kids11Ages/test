"""
Qifflt parser: hand-written recursive descent.

Expression precedence, loosest to tightest (per QIFFLT_SPEC.md):

    or
    and
    not
    == !=
    < > <= >=
    + -
    * / %
    unary -
    call / index (postfix)
    primary
"""

from __future__ import annotations

from . import ast_nodes as A
from .errors import QiffltError
from .lexer import TT, Token, tokenize

_BUILTIN_TOKEN_NAMES = {TT.SHOW: "show", TT.INPUT: "input"}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # -- token stream helpers -------------------------------------------------

    def _cur(self) -> Token:
        return self.tokens[self.pos]

    def _at(self, *types: TT) -> bool:
        return self._cur().type in types

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TT.EOF:
            self.pos += 1
        return tok

    def _expect(self, type_: TT, what: str) -> Token:
        if not self._at(type_):
            got = self._cur()
            raise QiffltError(
                f"unexpected token: expected {what}, got {got.value!r}", got.line
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._at(TT.NEWLINE):
            self._advance()

    def _end_of_statement(self) -> None:
        if self._at(TT.EOF) or self._at(TT.NEWLINE):
            self._skip_newlines()
            return
        got = self._cur()
        raise QiffltError(f"unexpected token: expected end of line, got {got.value!r}", got.line)

    # -- entry point ------------------------------------------------------------

    def parse_program(self) -> A.Program:
        line = self._cur().line
        stmts = []
        self._skip_newlines()
        while not self._at(TT.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        return A.Program(line, stmts)

    # -- statements ---------------------------------------------------------------

    def _block_until(self, *stop_types: TT) -> list[A.Node]:
        stmts = []
        self._skip_newlines()
        while not self._at(*stop_types) and not self._at(TT.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        return stmts

    def _statement(self) -> A.Node:
        tok = self._cur()

        if tok.type == TT.SET:
            return self._set_stmt()
        if tok.type == TT.IF:
            return self._if_stmt()
        if tok.type == TT.WHILE:
            return self._while_stmt()
        if tok.type == TT.FUNC:
            return self._func_def()
        if tok.type == TT.RETURN:
            return self._return_stmt()
        if tok.type == TT.IMPORT:
            return self._import_stmt()

        expr = self._expression()
        self._end_of_statement()
        return A.ExprStmt(tok.line, expr)

    def _set_stmt(self) -> A.Node:
        line = self._advance().line  # SET
        name_tok = self._expect(TT.IDENT, "identifier")
        value = self._expression()
        self._end_of_statement()
        return A.SetStmt(line, name_tok.value, value)

    def _if_stmt(self) -> A.Node:
        line = self._advance().line  # IF
        cond = self._expression()
        self._end_of_statement()
        then_body = self._block_until(TT.ELSE, TT.END)
        else_body: list[A.Node] = []
        if self._at(TT.ELSE):
            self._advance()
            self._end_of_statement()
            else_body = self._block_until(TT.END)
        self._expect(TT.END, "end")
        self._end_of_statement()
        return A.IfStmt(line, cond, then_body, else_body)

    def _while_stmt(self) -> A.Node:
        line = self._advance().line  # WHILE
        cond = self._expression()
        self._end_of_statement()
        body = self._block_until(TT.END)
        self._expect(TT.END, "end")
        self._end_of_statement()
        return A.WhileStmt(line, cond, body)

    def _func_def(self) -> A.Node:
        line = self._advance().line  # FUNC
        name_tok = self._expect(TT.IDENT, "function name")
        self._expect(TT.LPAREN, "'('")
        params: list[str] = []
        if not self._at(TT.RPAREN):
            params.append(self._expect(TT.IDENT, "parameter name").value)
            while self._at(TT.COMMA):
                self._advance()
                params.append(self._expect(TT.IDENT, "parameter name").value)
        self._expect(TT.RPAREN, "')'")
        self._end_of_statement()
        body = self._block_until(TT.END)
        self._expect(TT.END, "end")
        self._end_of_statement()
        return A.FuncDef(line, name_tok.value, params, body)

    def _return_stmt(self) -> A.Node:
        line = self._advance().line  # RETURN
        if self._at(TT.NEWLINE) or self._at(TT.EOF):
            self._end_of_statement()
            return A.ReturnStmt(line, None)
        value = self._expression()
        self._end_of_statement()
        return A.ReturnStmt(line, value)

    def _import_stmt(self) -> A.Node:
        line = self._advance().line  # IMPORT
        path_tok = self._expect(TT.STRING, "module path string")
        self._end_of_statement()
        return A.ImportStmt(line, path_tok.value)

    # -- expressions (precedence climbing) -----------------------------------------

    def _expression(self) -> A.Node:
        return self._or_expr()

    def _or_expr(self) -> A.Node:
        left = self._and_expr()
        while self._at(TT.OR):
            line = self._advance().line
            right = self._and_expr()
            left = A.BinaryOp(line, "or", left, right)
        return left

    def _and_expr(self) -> A.Node:
        left = self._not_expr()
        while self._at(TT.AND):
            line = self._advance().line
            right = self._not_expr()
            left = A.BinaryOp(line, "and", left, right)
        return left

    def _not_expr(self) -> A.Node:
        if self._at(TT.NOT):
            line = self._advance().line
            operand = self._not_expr()
            return A.UnaryOp(line, "not", operand)
        return self._equality_expr()

    def _equality_expr(self) -> A.Node:
        left = self._relational_expr()
        while self._at(TT.EQEQ, TT.NEQ):
            op_tok = self._advance()
            right = self._relational_expr()
            left = A.BinaryOp(op_tok.line, op_tok.value, left, right)
        return left

    def _relational_expr(self) -> A.Node:
        left = self._additive_expr()
        while self._at(TT.LT, TT.GT, TT.LE, TT.GE):
            op_tok = self._advance()
            right = self._additive_expr()
            left = A.BinaryOp(op_tok.line, op_tok.value, left, right)
        return left

    def _additive_expr(self) -> A.Node:
        left = self._multiplicative_expr()
        while self._at(TT.PLUS, TT.MINUS):
            op_tok = self._advance()
            right = self._multiplicative_expr()
            left = A.BinaryOp(op_tok.line, op_tok.value, left, right)
        return left

    def _multiplicative_expr(self) -> A.Node:
        left = self._unary_expr()
        while self._at(TT.STAR, TT.SLASH, TT.PERCENT):
            op_tok = self._advance()
            right = self._unary_expr()
            left = A.BinaryOp(op_tok.line, op_tok.value, left, right)
        return left

    def _unary_expr(self) -> A.Node:
        if self._at(TT.MINUS):
            line = self._advance().line
            operand = self._unary_expr()
            return A.UnaryOp(line, "-", operand)
        return self._postfix_expr()

    def _postfix_expr(self) -> A.Node:
        node = self._primary()
        while True:
            if self._at(TT.LPAREN):
                line = self._advance().line
                args = []
                if not self._at(TT.RPAREN):
                    args.append(self._expression())
                    while self._at(TT.COMMA):
                        self._advance()
                        args.append(self._expression())
                self._expect(TT.RPAREN, "')'")
                node = A.Call(line, node, args)
            elif self._at(TT.LBRACKET):
                line = self._advance().line
                idx = self._expression()
                self._expect(TT.RBRACKET, "']'")
                node = A.Index(line, node, idx)
            else:
                break
        return node

    def _primary(self) -> A.Node:
        tok = self._cur()

        if tok.type == TT.NUMBER:
            self._advance()
            return A.NumberLit(tok.line, tok.value)
        if tok.type == TT.STRING:
            self._advance()
            return A.StringLit(tok.line, tok.value)
        if tok.type == TT.TRUE:
            self._advance()
            return A.BoolLit(tok.line, True)
        if tok.type == TT.FALSE:
            self._advance()
            return A.BoolLit(tok.line, False)
        if tok.type == TT.NULL:
            self._advance()
            return A.NullLit(tok.line)
        if tok.type == TT.IDENT:
            self._advance()
            return A.Identifier(tok.line, tok.value)
        if tok.type in _BUILTIN_TOKEN_NAMES:
            self._advance()
            return A.Builtin(tok.line, _BUILTIN_TOKEN_NAMES[tok.type])
        if tok.type == TT.LPAREN:
            self._advance()
            expr = self._expression()
            self._expect(TT.RPAREN, "')'")
            return expr
        if tok.type == TT.LBRACKET:
            self._advance()
            items = []
            if not self._at(TT.RBRACKET):
                items.append(self._expression())
                while self._at(TT.COMMA):
                    self._advance()
                    items.append(self._expression())
            self._expect(TT.RBRACKET, "']'")
            return A.ListLit(tok.line, items)

        raise QiffltError(f"unexpected token: {tok.value!r}", tok.line)


def parse(source: str) -> A.Program:
    return Parser(tokenize(source)).parse_program()

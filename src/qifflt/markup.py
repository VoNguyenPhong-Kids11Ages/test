"""
Qifflt Markup — a hypertext markup language built on the same Qifflt
alphabet as the core language.

Tag and attribute names are spelled letter-by-letter using Qifflt glyphs
(see `alphabet.py`), so any HTML-ish tag name is expressible — there is
no fixed tag list. Delimiters are Qifflt's own brackets rather than
`< >`:

    《tagname attr="value"》 ... 《⁄tagname》      open ... close
    《tagname attr="value"⁄》                     self-closing
    《!-- ... --》                                 comment

Text content may be written as plain, ordinary text (used as-is), or as
a 「glyph string」 (see `alphabet.py`) that gets decoded before
rendering — i.e. markup content, too, can be authored entirely "in
Qifflt" while rendering out as completely normal HTML text.

A tag whose decoded name is `include` with a `src`/`href` attribute is
a hypertext transclusion: the referenced `.qfx` file is parsed and
rendered in place, so documents can link to and pull in other
documents — the actual "hypertext" in hypertext markup.
"""

from __future__ import annotations

import html as _html
import os
from dataclasses import dataclass, field

from . import alphabet
from .errors import QiffltError

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

_OPEN = "《"
_CLOSE = "》"
_SLASH = "⁄"


def _is_name_char(ch: str) -> bool:
    return ch.isalnum() or alphabet.is_glyph(ch)


@dataclass
class MarkupText:
    value: str


@dataclass
class MarkupElement:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


class _MarkupParser:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.n = len(source)

    def _line(self, pos: int) -> int:
        return 1 + self.src.count("\n", 0, pos)

    def _error(self, message: str, pos: int | None = None):
        raise QiffltError(message, self._line(self.pos if pos is None else pos))

    def parse(self) -> list:
        nodes = self._parse_nodes(stop_tag=None)
        if self.pos < self.n:
            self._error("unexpected closing tag with no matching open tag")
        return nodes

    def _parse_nodes(self, stop_tag: str | None) -> list:
        nodes: list = []
        while self.pos < self.n:
            if self.src.startswith(_OPEN + "!--", self.pos):
                self._skip_comment()
                continue

            if self.src.startswith(_OPEN + _SLASH, self.pos):
                start = self.pos
                self.pos += 2
                name = self._read_name()
                self._skip_ws()
                if self.pos >= self.n or self.src[self.pos] != _CLOSE:
                    self._error("unexpected token: expected '》' to close tag", start)
                self.pos += 1
                if stop_tag is None:
                    self._error(f"unexpected closing tag '{name}' with no open tag", start)
                if name != stop_tag:
                    self._error(
                        f"mismatched closing tag: expected '{stop_tag}', got '{name}'", start
                    )
                return nodes

            if self.src[self.pos] == _OPEN:
                nodes.append(self._parse_element())
                continue

            if self.src[self.pos] == "「":
                nodes.append(MarkupText(self._read_glyph_text()))
                continue

            nodes.append(MarkupText(self._read_plain_text()))

        if stop_tag is not None:
            self._error(f"unterminated tag: missing closing tag for '{stop_tag}'")
        return nodes

    def _skip_comment(self) -> None:
        end = self.src.find("--" + _CLOSE, self.pos)
        if end == -1:
            self._error("unterminated comment")
        self.pos = end + len("--" + _CLOSE)

    def _skip_ws(self) -> None:
        while self.pos < self.n and self.src[self.pos] in " \t\r\n":
            self.pos += 1

    def _read_name(self) -> str:
        start = self.pos
        while self.pos < self.n and _is_name_char(self.src[self.pos]):
            self.pos += 1
        if self.pos == start:
            self._error("unexpected token: expected a tag or attribute name")
        return alphabet.decode_tag_name(self.src[start:self.pos])

    def _read_quoted_value(self) -> str:
        if self.src[self.pos] == "「":
            return self._read_glyph_text()
        if self.src[self.pos] == '"':
            start = self.pos
            self.pos += 1
            end = self.src.find('"', self.pos)
            if end == -1:
                self._error("unterminated attribute value", start)
            value = self.src[self.pos:end]
            self.pos = end + 1
            return value
        self._error("unexpected token: expected a quoted or 「glyph」 attribute value")

    def _read_glyph_text(self) -> str:
        start = self.pos
        self.pos += 1  # skip 「
        end = self.src.find("」", self.pos)
        if end == -1:
            self._error("unterminated glyph string", start)
        raw = self.src[self.pos:end]
        self.pos = end + 1
        return alphabet.decode(raw)

    def _read_plain_text(self) -> str:
        start = self.pos
        while self.pos < self.n and self.src[self.pos] not in (_OPEN, "「"):
            self.pos += 1
        return self.src[start:self.pos]

    def _parse_element(self) -> MarkupElement:
        start = self.pos
        self.pos += 1  # skip 《
        tag = self._read_name()
        attrs: dict[str, str] = {}
        while True:
            self._skip_ws()
            if self.pos >= self.n:
                self._error("unterminated tag", start)
            ch = self.src[self.pos]
            if ch == _SLASH and self.src[self.pos:self.pos + 2] == _SLASH + _CLOSE:
                self.pos += 2
                return MarkupElement(tag, attrs, [])
            if ch == _CLOSE:
                self.pos += 1
                children = self._parse_nodes(stop_tag=tag)
                return MarkupElement(tag, attrs, children)
            if _is_name_char(ch):
                attr_name = self._read_name()
                self._skip_ws()
                if self.pos >= self.n or self.src[self.pos] != "=":
                    self._error("unexpected token: expected '=' after attribute name")
                self.pos += 1
                self._skip_ws()
                attrs[attr_name] = self._read_quoted_value()
                continue
            self._error(f"unexpected character {ch!r} inside tag")


def parse_markup(source: str) -> list:
    """Parse Qifflt Markup source into a list of top-level nodes."""
    return _MarkupParser(source).parse()


class _Renderer:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._stack: list[str] = []  # absolute paths currently being rendered

    def render_nodes(self, nodes: list) -> str:
        return "".join(self._render(n) for n in nodes)

    def _render(self, node) -> str:
        if isinstance(node, MarkupText):
            return _html.escape(node.value)

        assert isinstance(node, MarkupElement)
        if node.tag == "include":
            return self._render_include(node)

        attrs = "".join(
            f' {name}="{_html.escape(value, quote=True)}"' for name, value in node.attrs.items()
        )
        if node.tag in VOID_TAGS:
            return f"<{node.tag}{attrs}>"
        inner = "".join(self._render(c) for c in node.children)
        return f"<{node.tag}{attrs}>{inner}</{node.tag}>"

    def _render_include(self, node: MarkupElement) -> str:
        src = node.attrs.get("src") or node.attrs.get("href")
        if not src:
            raise QiffltError("'include' requires a 'src' or 'href' attribute")
        path = src if os.path.isabs(src) else os.path.join(self.base_dir, src)
        path = os.path.normpath(path)

        if path in self._stack:
            raise QiffltError(f"circular include detected: '{src}'")
        try:
            with open(path, "r", encoding="utf-8") as f:
                included_source = f.read()
        except OSError as exc:
            raise QiffltError(f"cannot include '{src}': {exc.strerror}")

        nodes = parse_markup(included_source)
        self._stack.append(path)
        previous_base_dir = self.base_dir
        self.base_dir = os.path.dirname(path) or "."
        try:
            return self.render_nodes(nodes)
        finally:
            self.base_dir = previous_base_dir
            self._stack.pop()


def render_html(source: str, base_dir: str | None = None) -> str:
    """Render Qifflt Markup source to an HTML string."""
    nodes = parse_markup(source)
    renderer = _Renderer(base_dir or os.getcwd())
    body = renderer.render_nodes(nodes)

    real_nodes = [
        n for n in nodes if not (isinstance(n, MarkupText) and not n.value.strip())
    ]
    if len(real_nodes) == 1 and isinstance(real_nodes[0], MarkupElement) and real_nodes[0].tag == "html":
        return "<!DOCTYPE html>\n" + body.strip() + "\n"
    return body

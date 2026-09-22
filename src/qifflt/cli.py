"""
Qifflt command-line interface.

    qifflt program.qft                    run a Qifflt program
    qifflt -c '₫1¥£!("Hello")'            run inline source
    qifflt run program.qft                 same as the bare form above
    qifflt html page.qfx [-o out.html]     render Qifflt Markup to HTML
    qifflt audio piece.qfa [-o out.wav]    render Qifflt Audio to a WAV file
    qifflt highlight program.qft           print source with syntax colors
    qifflt encode 'plain text'             convert text to the Qifflt alphabet
    qifflt decode '「...」' | 'cipher'      convert Qifflt-alphabet text back

Backward compatible: a bare file path is dispatched by its extension
(.qft/.qfx/.qfa run/html/audio respectively) exactly like naming the
subcommand explicitly, and `-c` still runs inline Qifflt source.
"""

from __future__ import annotations

import os
import sys

from . import alphabet
from .audio import render_audio
from .errors import QiffltError
from .highlighter import highlight as highlight_source
from .interpreter import Interpreter
from .markup import render_html
from .qparser import parse

USAGE = """usage:
  qifflt <file.qft>                 run a Qifflt program
  qifflt -c '<code>'                run inline Qifflt source
  qifflt run <file.qft>
  qifflt html <file.qfx> [-o FILE]  render Qifflt Markup to HTML
  qifflt audio <file.qfa> [-o FILE] render Qifflt Audio to a .wav file
  qifflt highlight <file.qft>       print source with syntax colors
  qifflt encode '<text>'            text -> Qifflt alphabet
  qifflt decode '<cipher>'          Qifflt alphabet -> text"""


def _read(path: str) -> str:
    if not os.path.isfile(path):
        print(f"qifflt: no such file: {path}", file=sys.stderr)
        raise SystemExit(2)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _output_path(args: list[str], default_ext: str, source_path: str) -> tuple[list[str], str]:
    """Pull a trailing '-o FILE' out of args; otherwise derive a default
    output path from the source file's name."""
    if "-o" in args:
        i = args.index("-o")
        if i + 1 >= len(args):
            print("qifflt: -o requires a file path", file=sys.stderr)
            raise SystemExit(2)
        out_path = args[i + 1]
        args = args[:i] + args[i + 2:]
        return args, out_path
    base, _ = os.path.splitext(source_path)
    return args, base + default_ext


def _run_file(path: str) -> int:
    source = _read(path)
    interp = Interpreter(base_dir=os.path.dirname(os.path.abspath(path)))
    interp.run(parse(source))
    return 0


def _run_inline(code: str) -> int:
    interp = Interpreter(base_dir=os.getcwd())
    interp.run(parse(code))
    return 0


def _cmd_html(args: list[str]) -> int:
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    args, out_path = _output_path(args, ".html", args[0])
    path = args[0]
    source = _read(path)
    html_out = render_html(source, base_dir=os.path.dirname(os.path.abspath(path)))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(out_path)
    return 0


def _cmd_audio(args: list[str]) -> int:
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    args, out_path = _output_path(args, ".wav", args[0])
    path = args[0]
    source = _read(path)
    duration = render_audio(source, out_path, base_dir=os.path.dirname(os.path.abspath(path)))
    print(f"{out_path} ({duration:.2f}s)")
    return 0


def _cmd_highlight(args: list[str]) -> int:
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    source = _read(args[0])
    use_color = sys.stdout.isatty() and "--no-color" not in args
    print(highlight_source(source, use_color=use_color), end="")
    return 0


def _cmd_encode(args: list[str]) -> int:
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    print(alphabet.encode(" ".join(args)))
    return 0


def _cmd_decode(args: list[str]) -> int:
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    text = " ".join(args).strip("「」")
    print(alphabet.decode(text))
    return 0


_EXT_DISPATCH = {".qfx": "html", ".qfa": "audio"}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if not argv:
        print(USAGE, file=sys.stderr)
        return 2

    try:
        if argv[0] == "-c":
            if len(argv) < 2:
                print(USAGE, file=sys.stderr)
                return 2
            return _run_inline(argv[1])

        if argv[0] == "run":
            if len(argv) < 2:
                print(USAGE, file=sys.stderr)
                return 2
            return _run_file(argv[1])

        if argv[0] == "html":
            return _cmd_html(argv[1:])
        if argv[0] == "audio":
            return _cmd_audio(argv[1:])
        if argv[0] == "highlight":
            return _cmd_highlight(argv[1:])
        if argv[0] == "encode":
            return _cmd_encode(argv[1:])
        if argv[0] == "decode":
            return _cmd_decode(argv[1:])

        # Bare file path: dispatch by extension (.qft/.qfx/.qfa), so
        # `qifflt page.qfx` behaves like `qifflt html page.qfx`.
        path = argv[0]
        _, ext = os.path.splitext(path)
        subcommand = _EXT_DISPATCH.get(ext)
        if subcommand == "html":
            return _cmd_html(argv)
        if subcommand == "audio":
            return _cmd_audio(argv)
        return _run_file(path)

    except QiffltError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

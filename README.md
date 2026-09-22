# Qifflt

Qifflt is three languages sharing one alphabet:

* **a programming language** (`.qft`) — no readable English keywords, ever;
* **a hypertext markup language** (`.qfx`) — renders to real HTML;
* **a hypertext audio language** (`.qfa`) — renders to a real, playable `.wav`.

All three are built from scratch (own lexer, parser, AST, interpreter/
renderers) — not Python, not HTML, wearing a costume — and all three are
spelled using **the Qifflt alphabet**: every keyword, tag, and attribute
has a deliberately opaque spelling, and any piece of text can be written
entirely in Qifflt glyphs while still decoding to completely ordinary,
readable output.

```
₫1¥£!("Hello, world!")
fpjrsidnvt("Hello, world!")     # exactly the same program
₫1¥£!(「♏☄☍☍☐‿☞☐☓☍☃⁘」)          # exactly the same output, spelled in glyphs
```

Qifflt is a sibling project to [Silem](https://pypi.org/project/silem/),
sharing its spirit of intentionally difficult syntax.

Full grammar, keyword tables, and semantics for all three languages live
in [`QIFFLT_SPEC.md`](./QIFFLT_SPEC.md).

## Installation

```bash
pip install qifflt
```

Or, from a local checkout:

```bash
pip install -e ".[dev]"            # + pytest, for running the test suite
pip install -e ".[highlight]"      # + pygments, for editor/doc-tool highlighting
```

## The Qifflt alphabet

Every Latin letter — lowercase and uppercase kept distinct — and common
punctuation has its own unique Qifflt glyph (`src/qifflt/alphabet.py`).
This is the one alphabet used everywhere in the project:

* in the core language, as a `「glyph string」` literal that decodes to a
  plain string at parse time — write your text entirely in Qifflt, run
  the program, get completely normal output;
* in Qifflt Markup, to spell tag and attribute names (`div`, `href`,
  `img`, `src`, ... — any tag name is expressible, there's no fixed list);
* in Qifflt Audio, the same way, plus as the alphabet a `speak` tag
  sonifies into tones.

```bash
qifflt encode 'Hello, world!'
# ♏☄☍☍☐⁙‿☞☐☓☍☃‼
qifflt decode '♏☄☍☍☐⁙‿☞☐☓☍☃‼'
# Hello, world!
```

Characters with no glyph (digits, Vietnamese diacritics, unmapped
punctuation, ...) pass straight through both `encode` and `decode`, so
plain and glyph text can always be freely mixed in the same literal.

## 1. The programming language (`.qft`)

```
₫1¥£!("Hello, world!")

1†Φ2 x 10
1₽53 x > 5
₫1¥£!("big")
Ω¥0¢
₫1¥£!("small")
±•₹£
```

```bash
qifflt hello.qft
qifflt -c '₫1¥£!("Hello, world!")'
```

### Keyword table

| Meaning | Symbol alias | Word alias |
|---|---|---|
| show | `₫1¥£!` | `fpjrsidnvt` |
| set | `1†Φ2` | `uzljmwgyv` |
| if | `1₽53` | `cqwvlmmzx` |
| else | `Ω¥0¢` | `ohfzkvwto` |
| end | `±•₹£` | `cnutbvaug` |
| while | `•₽÷•` | `oxzskaztk` |
| func | `5√£Ω` | `gtfqqqfyv` |
| return | `€97¥` | `zqpryuxlx` |
| true | `±±₹§` | `bfkcgorib` |
| false | `¶50£` | `njxebuolm` |
| null | `₹∆0±` | `wggepmtnr` |
| and | `±†√Φ` | `mtgzytnfw` |
| or | `8Ψ£¥` | `rtgunjyrk` |
| not | `30√Ω` | `osmumetiy` |
| input | `∞2₩7` | `wakcipqtm` |
| import | `₫+€×■@` | `vhqzomntyk` |

Any two programs using different aliases for the same keywords — symbol
or word, and now glyph strings for the text — are the same program.

**Functions, recursion, closures, lists, imports** all work as you'd
expect from a small language; see `examples/*.qft` and
`QIFFLT_SPEC.md` §1–§10 for the full tour. Two highlights:

```
# Text can be written entirely in the Qifflt alphabet and still prints
# as completely normal text.
1†Φ2 msg 「♏☄☍☍☐⁙‿☞☐☓☍☃‼」
₫1¥£!(msg)                        # -> Hello, world!
```

```
# import merges another file's top-level names into scope
₫+€×■@ "lib.qft"
₫1¥£!(square(6))
```

## 2. The hypertext markup language (`.qfx`)

Tags are spelled by writing the tag name letter-by-letter in the Qifflt
alphabet (or in plain ASCII — both work), inside Qifflt's own brackets:

```
《tagname attr="value"》 ... 《⁄tagname》      open ... close
《tagname attr="value"⁄》                     self-closing
《!-- ... --》                                 comment
```

```
《div》
  《h1》Welcome《⁄h1》
  《p》「♏☄☍☍☐⁙‿☞☐☓☍☃‼」《⁄p》
  《a href="https://example.com"》link《⁄a》
  《img src="pic.png"⁄》
《⁄div》
```

Renders to:

```html
<div>
<h1>Welcome</h1>
<p>Hello, world!</p>
<a href="https://example.com">link</a>
<img src="pic.png">
</div>
```

A tag named `include` (with `src`/`href`) transcludes another `.qfx`
file — the actual "hypertext" in hypertext markup — so pages can share
headers, footers, and components:

```
《include src="footer.qfx"⁄》
```

```bash
qifflt html page.qfx -o page.html
qifflt page.qfx                    # bare .qfx is dispatched to html automatically
```

See `examples/page.qfx` and `examples/footer.qfx` for a complete page,
and `QIFFLT_SPEC.md` §15 for the full grammar.

## 3. The hypertext audio language (`.qfa`)

Same alphabet, same `《tag》` syntax, interpreted as sound instead of
HTML, and rendered to a real mono 16-bit PCM `.wav` file using nothing
but the Python standard library:

```
《track》
  《note pitch="C4" dur="200"⁄》
  《note pitch="E4" dur="200"⁄》
  《note pitch="G4" dur="300"⁄》
  《rest dur="150"⁄》
  《repeat times="3"》
    《note freq="523.25" dur="120"⁄》
  《⁄repeat》
  《speak dur="140"》qifflt《⁄speak》
《⁄track》
```

* `note` — a tone: `pitch="A4"` (scientific pitch notation, `C4`…`B5`,
  sharps/flats with `#`/`b`) or `freq="440"` (Hz), plus `dur` in ms.
* `rest` — silence, in ms.
* `repeat times="N"` — replay its children N times.
* `speak` — **sonification**, not real text-to-speech: each letter of
  the text maps to a tone on a fixed two-octave scale, turning any
  phrase into a distinctive, fully original little melody.
* `include` — splice in another `.qfa` file, hypertext-style.

```bash
qifflt audio piece.qfa -o piece.wav
qifflt piece.qfa                   # bare .qfa is dispatched to audio automatically
```

See `examples/melody.qfa` and `QIFFLT_SPEC.md` §16 for the full grammar.

## Syntax highlighting

Three layers, all generated from (or verified against) the real
lexer/keyword tables, so they can't drift out of sync with the
language:

* **Terminal** — built in, no extra install:

  ```bash
  qifflt highlight program.qft
  ```

* **Pygments** — for Sphinx, mkdocs, and any other tool that already
  speaks Pygments:

  ```bash
  pip install "qifflt[highlight]"
  ```

  registers a `Qifflt` lexer for `.qft` / `.qfx` / `.qfa` automatically
  (see `src/qifflt/pygments_lexer.py`).

* **VS Code** — a TextMate grammar and language configuration under
  [`editors/vscode/`](./editors/vscode), generated straight from the
  keyword tables by [`tools/generate_vscode_grammar.py`](./tools/generate_vscode_grammar.py)
  (re-run it after changing any keyword alias, so the grammar can never
  go stale).

## CLI reference

```
qifflt <file.qft>                 run a Qifflt program
qifflt -c '<code>'                run inline Qifflt source
qifflt run <file.qft>             same as the bare form above
qifflt html <file.qfx> [-o FILE]  render Qifflt Markup to HTML
qifflt audio <file.qfa> [-o FILE] render Qifflt Audio to a .wav file
qifflt highlight <file.qft>       print source with syntax colors
qifflt encode '<text>'            text -> Qifflt alphabet
qifflt decode '<cipher>'          Qifflt alphabet -> text
```

A bare file path is also dispatched by its extension (`.qft` → run,
`.qfx` → html, `.qfa` → audio), and running with no arguments prints
usage and exits non-zero.

## Architecture

```
src/qifflt/
  alphabet.py        the Qifflt alphabet: letter/punctuation <-> glyph tables
  lexer.py            tokenizer + symbol/word keyword tables + glyph strings
  ast_nodes.py        AST node dataclasses
  qparser.py          recursive-descent parser
  interpreter.py      tree-walking interpreter, Environment, QiffltFunction
  markup.py           Qifflt Markup parser + HTML renderer (+ include)
  audio.py            Qifflt Audio parser + WAV synthesizer (+ include)
  highlighter.py       ANSI terminal syntax highlighting
  pygments_lexer.py   optional Pygments lexer (needs `qifflt[highlight]`)
  errors.py           QiffltError (user-facing) / QiffltReturn (internal signal)
  cli.py              command-line entry point (run/html/audio/highlight/encode/decode)
editors/vscode/       TextMate grammar + language config for VS Code
```

Each stage is independent and swappable. This modularity is intentional:
a future version may bootstrap a Qifflt implementation written in
[Silem](https://pypi.org/project/silem/) without needing to redesign the
language itself.

## Current limitations

* `import` merges names flatly — there's no namespaced module object or
  dot-member access yet in the core language.
* No string methods, no maps/dictionaries, no standard library beyond
  `show`/`input`.
* No bytecode compilation; the interpreter walks the AST directly.
* Qifflt Markup has no CSS/JS integration beyond what you inline as
  attributes/text — it's a document markup layer, not a browser engine.
* `speak` in Qifflt Audio is an original tone-per-letter sonification,
  not real speech synthesis.

See `QIFFLT_SPEC.md` §13 for the full list.

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [`LICENSE`](./LICENSE).

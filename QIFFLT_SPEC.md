# QIFFLT_SPEC.md — Qifflt 0.2.x Language Specification

Qifflt is three small, independent, from-scratch languages that share
one alphabet:

* the **core programming language** (`.qft`, §1–§14),
* **Qifflt Markup** (`.qfx`, §15), a hypertext markup language rendering
  to HTML, and
* **Qifflt Audio** (`.qfa`, §16), a hypertext audio language rendering
  to a real `.wav` file.

The defining trait of the core language is that **no keyword has a
readable English spelling**. Every keyword has exactly two valid
spellings ("aliases"):

* a **SYMBOL alias**, built from Unicode currency/math glyphs, and
* a **WORD alias**, an intentionally meaningless lowercase string.

The two aliases of a keyword are 100% behaviorally identical — the lexer
maps both spellings to the same token type, so the parser and interpreter
never see a difference. Plain English words like `if` or `show` are **not**
keywords in Qifflt; they lex as ordinary identifiers.

All three languages are implemented from scratch: their own lexers,
parsers, ASTs, and interpreter/renderers. None of them is Python or
HTML syntax in disguise.

## 1. Keyword table

| Meaning | SYMBOL alias | WORD alias |
|---|---|---|
| show (print) | `₫1¥£!` | `fpjrsidnvt` |
| set (assign) | `1†Φ2` | `uzljmwgyv` |
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

`import` is Qifflt's module-inclusion keyword (see §9). It follows the
same two-alias rule as every other keyword above.

## 2. Lexer

Tokens: symbol keywords, word keywords, `IDENT`, `NUMBER`, `STRING`,
`NEWLINE`, `EOF`, operators (`+ - * / % = == != < > <= >=`), and
punctuation (`( ) [ ] ,`). Comments start with `#` and run to end of line.

Symbol keywords are matched by **longest match** at the current lexer
position, so keywords that share a leading glyph (e.g. `if` and `set`
both start with `1`) are never confused with one another.

Word keywords are matched only as a **whole identifier** — `showtime`
lexes as the identifier `showtime`, not as the `show` keyword followed by
`time`.

A `「...」` literal (Japanese corner brackets, distinct from `"..."`) is
a **glyph string**: its contents are decoded through the Qifflt alphabet
(§14) right at lex time, producing an ordinary `STRING` token — the
parser and everything downstream never know the source was written in
glyphs. Unlike `"..."`, a glyph string may span multiple lines.

## 3. Grammar (informal)

```
program    := statement*
statement  := set_stmt | if_stmt | while_stmt | func_def
            | return_stmt | import_stmt | expr_stmt

set_stmt   := SET IDENT expr NEWLINE
if_stmt    := IF expr NEWLINE block (ELSE NEWLINE block)? END NEWLINE
while_stmt := WHILE expr NEWLINE block END NEWLINE
func_def   := FUNC IDENT '(' params? ')' NEWLINE block END NEWLINE
return_stmt:= RETURN expr? NEWLINE
import_stmt:= IMPORT STRING NEWLINE
expr_stmt  := expr NEWLINE

block      := statement*
params     := IDENT (',' IDENT)*
```

## 4. Expression precedence (loosest → tightest)

```
or
and
not
== !=
< > <= >=
+ -
* / %
unary -
call / index   (postfix)
primary
```

## 5. Data types

`number` (int/float), `string`, `boolean`, `null`, `list`.

```
₫1¥£!("Hello")
1†Φ2 x 10
₫1¥£!(x + 20)
```

## 6. Control flow

```
1₽53 x > 10
₫1¥£!("big")
Ω¥0¢
₫1¥£!("small")
±•₹£
```

```
•₽÷• i < 10
₫1¥£!(i)
1†Φ2 i i + 1
±•₹£
```

## 7. Functions

```
5√£Ω greet(name)
₫1¥£!("Hello", name)
±•₹£
```

```
5√£Ω square(n)
€97¥ n * n
±•₹£
```

Functions have parameters, a local environment, closures over their
defining scope, and strict argument-count checking.

## 8. Built-in `input`

```
1†Φ2 name ∞2₩7("Name: ")
```

Always returns a string.

## 9. Imports

```
₫+€×■@ "utils.qft"
```

`import` reads and runs another `.qft` file (resolved relative to the
importing file's directory) and merges every top-level name it defines
— variables and functions — into the importing scope, similar to
"from module import *". A given absolute path is only ever executed
once per program run, so re-importing the same file (directly or via a
cycle) is a harmless no-op.

## 10. Lists

```
[1, 2, 3]
items[0]
```

## 11. Errors

All Qifflt-level problems raise `QiffltError`, printed as:

```
Qifflt error (line 4): undefined variable 'x'
```

Recognized error kinds: unexpected character, unexpected token,
unterminated string, undefined variable, invalid function call, wrong
argument count, unknown operator, invalid indexing, division by zero,
and import failures. Ordinary Qifflt program errors never surface a raw
Python traceback.

## 12. CLI

```
qifflt program.qft
qifflt -c '₫1¥£!("Hello")'
```

Running with no arguments prints usage and exits with a non-zero status.

## 13. Current limitations (0.2.x)

* No dot-member access — `import` merges names flatly into scope rather
  than exposing a namespaced module object.
* No string methods, no float formatting controls beyond `%r`-style
  Python defaults, no dictionaries/maps.
* No standard library beyond `show` and `input`.
* Single-file interpreter; no bytecode compilation or optimization.
* `set` is define-or-update (it does not distinguish first assignment
  from reassignment, and there is no block-scoping below function
  scope).
* Qifflt Markup (§15) has no CSS/JS integration beyond attributes/text
  you inline yourself — it is a document markup layer, not a browser
  engine.
* Qifflt Audio's `speak` (§16) is an original tone-per-letter
  sonification, not real text-to-speech.

## 14. The Qifflt alphabet

Every Latin letter — lowercase and uppercase kept as separate glyph
sets, so case round-trips — and a handful of common punctuation marks
have their own unique Qifflt glyph (`src/qifflt/alphabet.py`,
`LOWER_GLYPHS` / `UPPER_GLYPHS` / `PUNCT_GLYPHS`). Characters with no
glyph (digits, Vietnamese diacritics, unmapped punctuation, ...) pass
through unchanged, so plain and glyph text can be freely mixed.

This is the one alphabet shared by all three Qifflt languages:

* In the **core language**, a `「...」` literal (delimited by Japanese
  corner brackets, distinct from `"..."`) is decoded from Qifflt glyphs
  to a plain string **at lex time**, becoming an ordinary `STRING`
  token — the parser and interpreter never know the source was glyphs.
  Unlike `"..."`, a glyph string may span multiple lines.

  ```
  1†Φ2 msg 「♏☄☍☍☐⁙‿☞☐☓☍☃‼」
  ₫1¥£!(msg)                    # -> Hello, world!
  ```

* In **Qifflt Markup** (§15) and **Qifflt Audio** (§16), tag and
  attribute names are spelled by writing their name letter-by-letter in
  the alphabet (plain ASCII letters also work — `decode_tag_name` just
  lowercases the result either way), and text content may use
  `「...」` glyph strings the same way as the core language.

`qifflt encode '<text>'` / `qifflt decode '<cipher>'` convert between
plain text and the Qifflt alphabet from the command line.

## 15. Qifflt Markup (`.qfx`)

A hypertext markup language sharing the Qifflt alphabet, rendering to
HTML. Delimiters are Qifflt's own brackets rather than `< >`:

```
document   := node*
node       := element | text | glyph_text | comment
element    := open_tag node* close_tag | self_closing_tag
open_tag   := 《 tagname attr* 》
close_tag  := 《⁄ tagname 》
self_closing_tag := 《 tagname attr* ⁄》
attr       := name '=' ( '"' ... '"' | glyph_text )
tagname    := (letter-glyph | ASCII letter | digit)+
comment    := 《!-- ... --》
text       := any run of characters outside 《 》 and 「 」, used as-is
glyph_text := 「 ... 」, decoded before rendering
```

* Tag/attribute names have **no fixed list** — any HTML-ish name is
  expressible, since the name is just the Qifflt-alphabet spelling of
  an ordinary word (`div`, `href`, `h1`, `strong`, ...).
* Void elements (`br`, `hr`, `img`, `input`, `meta`, `link`, `source`,
  `area`, `base`, `col`, `embed`, `track`, `wbr`) always render without
  a closing tag, regardless of how they were written.
* A single top-level `html` element gets a `<!DOCTYPE html>` prefix;
  otherwise the rendered nodes are returned as an HTML fragment.
* A tag named `include`, with a `src` or `href` attribute, transcludes
  another `.qfx` file at that point (resolved relative to the
  including file's directory; a given file may not include itself,
  directly or via a cycle). This is the "hypertext" in hypertext
  markup — pages linking to and pulling in other documents.
* Plain text outside `《 》`/`「 」` is used as-is (not decoded) and is
  HTML-escaped on render, same as `「glyph text」` content.

```
《html》
《head》《title》「♔♡‿♘☊☇☇☍☛‿♗☀☈☄」《⁄title》《⁄head》
《body》
《h1》Qifflt Markup《⁄h1》
《p》Plain text works too.《⁄p》
《a href="https://example.com"》link《⁄a》
《img src="pic.png"⁄》
《include src="footer.qfx"⁄》
《⁄body》
《⁄html》
```

```bash
qifflt html page.qfx -o page.html
qifflt page.qfx                    # bare .qfx dispatches to html automatically
```

## 16. Qifflt Audio (`.qfa`)

A hypertext audio language, sharing Qifflt Markup's tag syntax and
alphabet but interpreted as sound, rendered to a real mono 16-bit PCM
`.wav` file (44.1 kHz, sine-wave synthesis with a short fade in/out per
event to avoid clicks) using only the Python standard library.

Recognized tags:

| Tag | Attributes | Meaning |
|---|---|---|
| `track` | — | a grouping of sound events (purely structural) |
| `repeat` | `times="N"` | replay its children N times |
| `note` | `pitch="A4"` or `freq="440"`, `dur` (ms, default 300) | a tone. `pitch` uses scientific pitch notation: a letter `A`-`G`, optional `#`/`b`, then an octave number (`C4`, `D#5`, `Bb3`, ...) |
| `rest` | `dur` (ms, default 300) | silence |
| `speak` | `dur` (ms per letter, default 150) | **sonification**: each letter of the text content maps to a tone on a fixed two-octave chromatic scale starting at middle C (`a`=C4, `b`=C#4, ... wrapping past `z`), with a short gap between letters. This is a deterministic, fully original tone mapping — not real speech synthesis. |
| `include` | `src`/`href` | splice in another `.qfa` file (same rules as Markup's `include`) |

Any other tag name is a `QiffltError: unknown audio tag`. Text content
is only meaningful inside `speak`; plain text elsewhere is an error.

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

```bash
qifflt audio piece.qfa -o piece.wav
qifflt piece.qfa                   # bare .qfa dispatches to audio automatically
```

## 17. Syntax highlighting

Three integrations, all generated from or verified against the real
lexer/keyword tables so they cannot drift out of sync with the
language itself:

* **Terminal** (`qifflt highlight file.qft`, `src/qifflt/highlighter.py`)
  — walks the real `Lexer` token stream and wraps each token in ANSI
  color codes; comments are colored separately since the lexer
  discards them. Stripping the ANSI codes back out always reproduces
  the original source exactly.
* **Pygments** (`src/qifflt/pygments_lexer.py`, optional —
  `pip install qifflt[highlight]`) — a `RegexLexer` built directly from
  `SYMBOL_KEYWORDS`/`WORD_KEYWORDS`, registered as a `pygments.lexers`
  entry point for `.qft`/`.qfx`/`.qfa`, for Sphinx, mkdocs, and any
  other Pygments-based tool.
* **VS Code** (`editors/vscode/`) — a TextMate grammar
  (`syntaxes/qifflt.tmLanguage.json`) and language configuration,
  generated by `tools/generate_vscode_grammar.py` directly from the
  same keyword tables. Re-run that script after changing any keyword
  alias.

## 18. Roadmap direction (not yet implemented)

The interpreter and renderers are deliberately organized as
independent lexer / parser / AST / interpreter / markup / audio / CLI
modules so that a future version can swap the backend — for example,
bootstrapping a Qifflt implementation written in
[Silem](https://pypi.org/project/silem/) — without redesigning any of
the three languages.

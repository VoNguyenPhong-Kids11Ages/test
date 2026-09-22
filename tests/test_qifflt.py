import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt import Interpreter, QiffltError, parse  # noqa: E402


def run(code: str, inputs=None, base_dir=None):
    """Run Qifflt source, capturing show() output as a list of lines and
    feeding `inputs` to input() in order."""
    outputs = []
    inputs = iter(inputs or [])

    def fake_input(prompt=""):
        return next(inputs)

    interp = Interpreter(base_dir=base_dir, input_fn=fake_input, output_fn=outputs.append)
    interp.run(parse(code))
    return outputs


# ---------------------------------------------------------------------------
# Hello world
# ---------------------------------------------------------------------------

def test_hello_world_symbol():
    assert run('₫1¥£!("Hello world")') == ["Hello world"]


def test_hello_world_word():
    assert run('fpjrsidnvt("Hello world")') == ["Hello world"]


def test_symbol_and_word_are_equivalent():
    assert run('₫1¥£!("Hello")') == run('fpjrsidnvt("Hello")')


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

def test_arithmetic():
    out = run("""
1†Φ2 x 10
₫1¥£!(x + 20)
₫1¥£!(x - 3)
₫1¥£!(x * 2)
₫1¥£!(x / 2)
₫1¥£!(x % 3)
""")
    assert out == ["30", "7", "20", "5", "1"]


def test_division_by_zero_is_qifflt_error():
    with pytest.raises(QiffltError):
        run("₫1¥£!(1 / 0)")


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

def test_variables():
    out = run("""
1†Φ2 x 1
1†Φ2 x x + 1
₫1¥£!(x)
""")
    assert out == ["2"]


def test_undefined_variable_error():
    with pytest.raises(QiffltError) as exc:
        run("₫1¥£!(nope)")
    assert "undefined variable" in str(exc.value)


# ---------------------------------------------------------------------------
# if / else
# ---------------------------------------------------------------------------

def test_if_else_true_branch():
    out = run("""
1₽53 ±±₹§
₫1¥£!("yes")
Ω¥0¢
₫1¥£!("no")
±•₹£
""")
    assert out == ["yes"]


def test_if_else_false_branch():
    out = run("""
1₽53 ¶50£
₫1¥£!("yes")
Ω¥0¢
₫1¥£!("no")
±•₹£
""")
    assert out == ["no"]


# ---------------------------------------------------------------------------
# while
# ---------------------------------------------------------------------------

def test_while_loop():
    out = run("""
1†Φ2 i 0
•₽÷• i < 3
₫1¥£!(i)
1†Φ2 i i + 1
±•₹£
""")
    assert out == ["0", "1", "2"]


# ---------------------------------------------------------------------------
# functions / return / recursion
# ---------------------------------------------------------------------------

def test_function_and_return():
    out = run("""
5√£Ω add(a, b)
€97¥ a + b
±•₹£
₫1¥£!(add(2, 3))
""")
    assert out == ["5"]


def test_recursion():
    out = run("""
5√£Ω fact(n)
1₽53 n <= 1
€97¥ 1
±•₹£
€97¥ n * fact(n - 1)
±•₹£
₫1¥£!(fact(6))
""")
    assert out == ["720"]


def test_wrong_argument_count():
    with pytest.raises(QiffltError) as exc:
        run("""
5√£Ω add(a, b)
€97¥ a + b
±•₹£
add(1)
""")
    assert "wrong argument count" in str(exc.value)


def test_closures():
    out = run("""
5√£Ω make_adder(n)
5√£Ω adder(x)
€97¥ x + n
±•₹£
€97¥ adder
±•₹£
1†Φ2 add5 make_adder(5)
₫1¥£!(add5(10))
""")
    assert out == ["15"]


# ---------------------------------------------------------------------------
# lists / indexing
# ---------------------------------------------------------------------------

def test_lists_and_indexing():
    out = run("""
1†Φ2 items [10, 20, 30]
₫1¥£!(items[0])
₫1¥£!(items[2])
""")
    assert out == ["10", "30"]


def test_invalid_indexing():
    with pytest.raises(QiffltError) as exc:
        run("""
1†Φ2 items [1, 2, 3]
₫1¥£!(items[10])
""")
    assert "invalid indexing" in str(exc.value)


# ---------------------------------------------------------------------------
# input
# ---------------------------------------------------------------------------

def test_input_builtin():
    out = run("""
1†Φ2 name ∞2₩7("Name: ")
₫1¥£!("Hi", name)
""", inputs=["An"])
    assert out == ["Hi An"]


def test_input_word_alias():
    out = run("""
1†Φ2 name wakcipqtm("Name: ")
fpjrsidnvt("Hi", name)
""", inputs=["Lam"])
    assert out == ["Hi Lam"]


# ---------------------------------------------------------------------------
# syntax errors
# ---------------------------------------------------------------------------

def test_unexpected_character():
    with pytest.raises(QiffltError) as exc:
        run("1†Φ2 x @")
    assert "unexpected character" in str(exc.value)


def test_unterminated_string():
    with pytest.raises(QiffltError) as exc:
        run('₫1¥£!("oops)')
    assert "unterminated string" in str(exc.value)


def test_unexpected_token():
    with pytest.raises(QiffltError) as exc:
        run("1₽53")
    assert "unexpected token" in str(exc.value)


# ---------------------------------------------------------------------------
# symbol vs word keyword coverage
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,word", [
    ("±±₹§", "bfkcgorib"),
    ("¶50£", "njxebuolm"),
])
def test_bool_literal_aliases_match(symbol, word):
    assert run(f"₫1¥£!({symbol})") == run(f"₫1¥£!({word})")


def test_null_literal():
    assert run("₫1¥£!(₹∆0±)") == ["null"]
    assert run("₫1¥£!(wggepmtnr)") == ["null"]


def test_and_or_not():
    out = run("""
₫1¥£!(±±₹§ ±†√Φ ¶50£)
₫1¥£!(±±₹§ 8Ψ£¥ ¶50£)
₫1¥£!(30√Ω ¶50£)
""")
    assert out == ["false", "true", "true"]


# ---------------------------------------------------------------------------
# import
# ---------------------------------------------------------------------------

def test_import_symbol_alias(tmp_path):
    lib = tmp_path / "lib.qft"
    lib.write_text('5√£Ω square(n)\n€97¥ n * n\n±•₹£\n1†Φ2 GREETING "hi"\n', encoding="utf-8")
    out = run('''
₫+€×■@ "lib.qft"
₫1¥£!(square(4))
₫1¥£!(GREETING)
''', base_dir=str(tmp_path))
    assert out == ["16", "hi"]


def test_import_word_alias(tmp_path):
    lib = tmp_path / "lib.qft"
    lib.write_text('5√£Ω cube(n)\n€97¥ n * n * n\n±•₹£\n', encoding="utf-8")
    out = run('''
vhqzomntyk "lib.qft"
fpjrsidnvt(cube(3))
''', base_dir=str(tmp_path))
    assert out == ["27"]


def test_import_is_idempotent(tmp_path):
    lib = tmp_path / "lib.qft"
    lib.write_text('₫1¥£!("loaded")\n', encoding="utf-8")
    out = run('''
₫+€×■@ "lib.qft"
₫+€×■@ "lib.qft"
''', base_dir=str(tmp_path))
    assert out == ["loaded"]


def test_import_missing_file(tmp_path):
    with pytest.raises(QiffltError) as exc:
        run('₫+€×■@ "does_not_exist.qft"', base_dir=str(tmp_path))
    assert "cannot import" in str(exc.value)

import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJECT_ROOT, "src")


def run_cli(args, cwd=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "qifflt.cli", *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


def test_cli_inline_code():
    result = run_cli(["-c", '₫1¥£!("Hello world")'])
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello world"


def test_cli_word_alias_inline():
    result = run_cli(["-c", 'fpjrsidnvt("Hello world")'])
    assert result.returncode == 0
    assert result.stdout.strip() == "Hello world"


def test_cli_no_args_prints_usage_and_nonzero_exit():
    result = run_cli([])
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()


def test_cli_missing_file():
    result = run_cli(["does_not_exist.qft"])
    assert result.returncode != 0


def test_cli_runtime_error_is_clean():
    result = run_cli(["-c", "₫1¥£!(1 / 0)"])
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "Qifflt error" in result.stderr


def test_cli_runs_file(tmp_path):
    program = tmp_path / "hello.qft"
    program.write_text('₫1¥£!("from file")\n', encoding="utf-8")
    result = run_cli([str(program)])
    assert result.returncode == 0
    assert result.stdout.strip() == "from file"


def test_cli_file_with_import(tmp_path):
    (tmp_path / "lib.qft").write_text(
        '5√£Ω double(n)\n€97¥ n * 2\n±•₹£\n', encoding="utf-8"
    )
    main = tmp_path / "main.qft"
    main.write_text('₫+€×■@ "lib.qft"\n₫1¥£!(double(21))\n', encoding="utf-8")
    result = run_cli([str(main)])
    assert result.returncode == 0
    assert result.stdout.strip() == "42"


def _tag(name):
    from qifflt import alphabet
    return alphabet.encode(name)


def test_cli_encode_decode_roundtrip():
    enc = run_cli(["encode", "Hello", "world"])
    assert enc.returncode == 0
    cipher = enc.stdout.strip()
    dec = run_cli(["decode", cipher])
    assert dec.returncode == 0
    assert dec.stdout.strip() == "Hello world"


def test_cli_highlight_no_color_without_tty():
    program = "₫1¥£!(\"hi\")\n"
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".qft", delete=False) as f:
        f.write(program)
        path = f.name
    try:
        result = run_cli(["highlight", path])
        assert result.returncode == 0
        assert result.stdout == program
    finally:
        os.remove(path)


def test_cli_html_subcommand(tmp_path):
    page = tmp_path / "page.qfx"
    page.write_text(f"《{_tag('p')}》Hi《⁄{_tag('p')}》", encoding="utf-8")
    result = run_cli(["html", str(page)])
    assert result.returncode == 0
    out_path = tmp_path / "page.html"
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8") == "<p>Hi</p>"


def test_cli_bare_qfx_dispatches_to_html(tmp_path):
    page = tmp_path / "page.qfx"
    page.write_text(f"《{_tag('p')}》Hi《⁄{_tag('p')}》", encoding="utf-8")
    result = run_cli([str(page)])
    assert result.returncode == 0
    assert (tmp_path / "page.html").exists()


def test_cli_audio_subcommand(tmp_path):
    piece = tmp_path / "beep.qfa"
    piece.write_text(
        f'《{_tag("note")} {_tag("pitch")}="A4" {_tag("dur")}="100"⁄》', encoding="utf-8"
    )
    result = run_cli(["audio", str(piece)])
    assert result.returncode == 0
    assert (tmp_path / "beep.wav").exists()


def test_cli_bare_qfa_dispatches_to_audio(tmp_path):
    piece = tmp_path / "beep.qfa"
    piece.write_text(
        f'《{_tag("note")} {_tag("pitch")}="A4" {_tag("dur")}="100"⁄》', encoding="utf-8"
    )
    result = run_cli([str(piece)])
    assert result.returncode == 0
    assert (tmp_path / "beep.wav").exists()

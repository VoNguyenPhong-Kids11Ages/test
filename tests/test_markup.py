import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from qifflt import QiffltError, alphabet  # noqa: E402
from qifflt.markup import render_html  # noqa: E402


def tag(name: str) -> str:
    return alphabet.encode(name)


def test_simple_element_renders_to_html():
    src = f"《{tag('p')}》Hello《⁄{tag('p')}》"
    assert render_html(src) == "<p>Hello</p>"


def test_word_alias_style_plain_ascii_tag_names_also_work():
    # Tag names may be spelled with plain ASCII letters too (decode_tag_name
    # just lowercases them), not only Qifflt glyphs.
    src = "《div》Hi《⁄div》"
    assert render_html(src) == "<div>Hi</div>"


def test_attributes_render_with_values():
    src = f'《{tag("a")} {tag("href")}="https://example.com"》link《⁄{tag("a")}》'
    assert render_html(src) == '<a href="https://example.com">link</a>'


def test_glyph_text_content_decodes():
    text = alphabet.encode("Qifflt rocks")
    src = f"《{tag('p')}》「{text}」《⁄{tag('p')}》"
    assert render_html(src) == "<p>Qifflt rocks</p>"


def test_void_tags_self_close_without_closing_tag():
    src = f'《{tag("img")} {tag("src")}="a.png"⁄》'
    assert render_html(src) == '<img src="a.png">'


def test_self_closing_non_void_tag_becomes_empty_element():
    src = f'《{tag("div")}⁄》'
    assert render_html(src) == "<div></div>"


def test_nested_elements():
    src = f"《{tag('div')}》《{tag('p')}》A《⁄{tag('p')}》《{tag('p')}》B《⁄{tag('p')}》《⁄{tag('div')}》"
    assert render_html(src) == "<div><p>A</p><p>B</p></div>"


def test_html_root_gets_doctype():
    src = f"《{tag('html')}》《{tag('body')}》Hi《⁄{tag('body')}》《⁄{tag('html')}》"
    out = render_html(src)
    assert out.startswith("<!DOCTYPE html>\n")
    assert "<html><body>Hi</body></html>" in out


def test_comment_is_ignored():
    src = f"《!-- note --》《{tag('p')}》Hi《⁄{tag('p')}》"
    assert render_html(src) == "<p>Hi</p>"


def test_text_is_html_escaped():
    src = f"《{tag('p')}》A & B < C《⁄{tag('p')}》"
    assert render_html(src) == "<p>A &amp; B &lt; C</p>"


def test_mismatched_closing_tag_is_qifflt_error():
    src = f"《{tag('div')}》Hi《⁄{tag('span')}》"
    with pytest.raises(QiffltError) as exc:
        render_html(src)
    assert "mismatched closing tag" in str(exc.value)


def test_unterminated_tag_is_qifflt_error():
    with pytest.raises(QiffltError) as exc:
        render_html(f"《{tag('div')}》Hi")
    assert "unterminated" in str(exc.value)


def test_include_transcludes_another_file(tmp_path):
    (tmp_path / "footer.qfx").write_text(
        f"《{tag('p')}》Footer《⁄{tag('p')}》", encoding="utf-8"
    )
    main_src = (
        f'《{tag("div")}》《{tag("include")} {tag("src")}="footer.qfx"⁄》《⁄{tag("div")}》'
    )
    out = render_html(main_src, base_dir=str(tmp_path))
    assert out == "<div><p>Footer</p></div>"


def test_include_missing_file_is_qifflt_error(tmp_path):
    src = f'《{tag("include")} {tag("src")}="nope.qfx"⁄》'
    with pytest.raises(QiffltError) as exc:
        render_html(src, base_dir=str(tmp_path))
    assert "cannot include" in str(exc.value)

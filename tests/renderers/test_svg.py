import re

import pytest

from gtr_scaler.domain.fretboard import degree_fret_start
from gtr_scaler.domain.scales import get_scale
from gtr_scaler.renderers.svg import (
    render_multi_svg,
    render_svg,
    save_multi_pdf,
    save_multi_svg,
    save_pdf,
)


def test_render_multi_svg_stacks_two_diagrams():
    scale = get_scale("pentatonic_minor")
    fret_start_1 = degree_fret_start("A", scale, 1)
    fret_start_2 = degree_fret_start("A", scale, 2)
    diagrams = [
        ("A", scale, fret_start_1, 12, 3),
        ("A", scale, fret_start_2, 12, 3),
    ]
    result = render_multi_svg(diagrams)

    assert result.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    # Count nested <svg tags after the master opening tag
    first_svg_end = result.index(">") + 1
    nested_count = result[first_svg_end:].count("<svg")
    assert nested_count == 2
    # No internal XML declarations
    assert "<?xml" not in result
    # y="0" for the first diagram, larger y for the second
    assert 'y="0"' in result
    # Find all y= values and verify at least one is > 0
    y_values = [int(m) for m in re.findall(r'y="(\d+)"', result)]
    assert 0 in y_values
    assert any(v > 0 for v in y_values)


def test_save_multi_svg_creates_file(tmp_path):
    scale = get_scale("pentatonic_minor")
    fret_start_1 = degree_fret_start("A", scale, 1)
    fret_start_2 = degree_fret_start("A", scale, 3)
    diagrams = [
        ("A", scale, fret_start_1, 12, 3),
        ("A", scale, fret_start_2, 12, 3),
    ]
    out = tmp_path / "multi.svg"
    save_multi_svg(str(out), diagrams)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "</svg>" in content


def test_render_svg_with_title():
    scale = get_scale("pentatonic_minor")
    svg = render_svg("A", scale, 0, 12, title="A Pentatonic Minor")
    # Title text element should be present
    assert "<text" in svg
    assert "A Pentatonic Minor" in svg
    # Height should be increased by _TITLE_HEIGHT (60)
    m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
    assert m_h is not None
    height = float(m_h.group(1))
    # Without title, height would be the fretboard width (280).
    # With title, it should be 280 + 60 = 340.
    assert height == 340.0


def test_render_svg_no_title():
    scale = get_scale("pentatonic_minor")
    svg = render_svg("A", scale, 0, 12)
    # No title-specific <text> element (font-size="16" is only used by titles)
    assert 'font-size="16"' not in svg
    # Height should be the standard fretboard width (280)
    m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
    assert m_h is not None
    height = float(m_h.group(1))
    assert height == 280.0


def test_render_multi_svg_with_titles():
    scale = get_scale("pentatonic_minor")
    fret_start_1 = degree_fret_start("A", scale, 1)
    fret_start_2 = degree_fret_start("A", scale, 2)
    diagrams = [
        ("A", scale, fret_start_1, 12, 3),
        ("A", scale, fret_start_2, 12, 3),
    ]
    titles = ["A Pentatonic Minor — Shape 1", "A Pentatonic Minor — Shape 2"]
    result = render_multi_svg(diagrams, titles=titles)
    assert "Shape 1" in result
    assert "Shape 2" in result
    # Both titles should appear as title-specific <text> elements (font-size="16")
    assert result.count('font-size="16"') == 2


def test_render_multi_svg_titles_length_mismatch():
    scale = get_scale("pentatonic_minor")
    diagrams = [
        ("A", scale, 0, 12, 3),
        ("A", scale, 5, 12, 3),
    ]
    with pytest.raises(ValueError, match="titles length"):
        render_multi_svg(diagrams, titles=["only one"])


def test_save_multi_svg_with_titles(tmp_path):
    scale = get_scale("pentatonic_minor")
    fret_start_1 = degree_fret_start("A", scale, 1)
    fret_start_2 = degree_fret_start("A", scale, 2)
    diagrams = [
        ("A", scale, fret_start_1, 12, 3),
        ("A", scale, fret_start_2, 12, 3),
    ]
    titles = ["A Pentatonic Minor — Shape 1", "A Pentatonic Minor — Shape 2"]
    out = tmp_path / "titled.svg"
    save_multi_svg(str(out), diagrams, titles=titles)
    content = out.read_text(encoding="utf-8")
    assert "Shape 1" in content
    assert "Shape 2" in content


def _cairo_available() -> bool:
    """Check if cairosvg can actually be imported (native lib present)."""
    try:
        import cairosvg  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


def test_save_pdf_single_with_title(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    scale = get_scale("pentatonic_minor")
    out = tmp_path / "titled.pdf"
    save_pdf(str(out), "A", scale, 0, 12, title="A Pentatonic Minor")
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")


def test_save_multi_pdf_paginated_5_diagrams(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    scale = get_scale("pentatonic_minor")
    diagrams = []
    titles = []
    for deg in range(1, 6):
        fs = degree_fret_start("A", scale, deg)
        diagrams.append(("A", scale, fs, 12, 3))
        titles.append(f"A Pentatonic Minor — Shape {deg}")

    out = tmp_path / "multi.pdf"
    save_multi_pdf(str(out), diagrams, titles=titles, max_per_page=3)
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")

    reader = PdfReader(str(out))
    # 5 diagrams with max_per_page=3 → 2 pages
    assert len(reader.pages) == 2


def test_render_svg_title_inside_svg_root():
    scale = get_scale("pentatonic_minor")
    svg = render_svg("A", scale, 0, 12, title="A Pentatonic Minor")
    svg_open_end = svg.index(">", svg.index("<svg")) + 1
    svg_close_start = svg.rindex("</svg>")
    inner = svg[svg_open_end:svg_close_start]
    assert "<text" in inner, "Title <text> must be inside <svg> root element"


def test_render_multi_svg_titles_inside_nested_svgs():
    scale = get_scale("pentatonic_minor")
    fret_start_1 = degree_fret_start("A", scale, 1)
    fret_start_2 = degree_fret_start("A", scale, 2)
    diagrams = [
        ("A", scale, fret_start_1, 12, 3),
        ("A", scale, fret_start_2, 12, 3),
    ]
    titles = ["Shape 1", "Shape 2"]
    result = render_multi_svg(diagrams, titles=titles)

    # Split by nested <svg occurrences after the master opening tag
    first_svg_end = result.index(">") + 1
    rest = result[first_svg_end:]
    # Each nested diagram should contain its title text inside its own <svg>...</svg>
    nested_svgs = rest.split("<svg")[1:]  # skip empty first split
    assert len(nested_svgs) == 2
    for i, nested in enumerate(nested_svgs):
        close_idx = nested.index("</svg>")
        inner = nested[:close_idx]
        assert "<text" in inner
        assert titles[i] in inner


def test_save_multi_pdf_7_diagrams(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    scale = get_scale("major")
    diagrams = []
    titles = []
    for deg in range(1, 8):
        fs = degree_fret_start("C", scale, deg)
        diagrams.append(("C", scale, fs, 12, 3))
        titles.append(f"C Major — Shape {deg}")

    out = tmp_path / "multi.pdf"
    save_multi_pdf(str(out), diagrams, titles=titles, max_per_page=3)
    assert out.exists()

    reader = PdfReader(str(out))
    # 7 diagrams with max_per_page=3 → 3 pages
    assert len(reader.pages) == 3

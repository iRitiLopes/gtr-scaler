import re

import pytest

from gtr_scaler.diagram_params import DiagramData
from gtr_scaler.domain.fretboard import FretboardProjector
from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import ScaleCatalog
from gtr_scaler.exporters.file_writer import FileWriter
from gtr_scaler.exporters.pdf import MultiPagePdfBuilder, PdfConverter
from gtr_scaler.renderers.multi import MultiDiagramRenderer
from gtr_scaler.renderers.svg import SvgPostProcessor, SvgRenderer

notes = NoteService()
catalog = ScaleCatalog(notes)
projector = FretboardProjector(notes)
svg_renderer = SvgRenderer()
svg_post_processor = SvgPostProcessor()
multi_renderer = MultiDiagramRenderer(svg_renderer, svg_post_processor)
pdf_converter = PdfConverter()
pdf_builder = MultiPagePdfBuilder(svg_renderer, multi_renderer, pdf_converter)
file_writer = FileWriter()


def _make_data(root: str, scale, fret_start: int, fret_end: int, notes_per_string: int | None = None, title: str | None = None) -> DiagramData:
    """Helper to build DiagramData for tests."""
    if notes_per_string is not None:
        cells, fe = projector.project_n_notes(root, scale, notes_per_string, fret_start)
    else:
        cells = projector.project(root, scale, fret_start, fret_end)
        fe = fret_end
    t = title or f"{root} {scale.display_name}"
    return DiagramData(cells=cells, fret_start=fret_start, fret_end=fe, title=t)


def test_render_multi_svg_stacks_two_diagrams():
    scale = catalog.get("pentatonic_minor")
    ds1 = _make_data("A", scale, projector.degree_fret_start("A", scale, 1), 12, notes_per_string=3)
    ds2 = _make_data("A", scale, projector.degree_fret_start("A", scale, 2), 12, notes_per_string=3)
    diagrams = [ds1, ds2]
    result = multi_renderer.render(diagrams)

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
    scale = catalog.get("pentatonic_minor")
    ds1 = _make_data("A", scale, projector.degree_fret_start("A", scale, 1), 12, notes_per_string=3)
    ds2 = _make_data("A", scale, projector.degree_fret_start("A", scale, 3), 12, notes_per_string=3)
    diagrams = [ds1, ds2]
    out = tmp_path / "multi.svg"
    svg = multi_renderer.render(diagrams)
    file_writer.write_text(str(out), svg)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "</svg>" in content


def test_render_svg_with_title():
    scale = catalog.get("pentatonic_minor")
    data = _make_data("A", scale, 0, 12, title="A Pentatonic Minor")
    raw = svg_renderer.render(data.cells, data.fret_start, data.fret_end)
    svg = svg_post_processor.process(raw, data.title)
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
    scale = catalog.get("pentatonic_minor")
    data = _make_data("A", scale, 0, 12)
    raw = svg_renderer.render(data.cells, data.fret_start, data.fret_end)
    svg = svg_post_processor.process(raw)
    # No title-specific <text> element (font-size="16" is only used by titles)
    assert 'font-size="16"' not in svg
    # Height should be the standard fretboard width (280)
    m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
    assert m_h is not None
    height = float(m_h.group(1))
    assert height == 280.0


def test_render_multi_svg_with_titles():
    scale = catalog.get("pentatonic_minor")
    ds1 = _make_data("A", scale, projector.degree_fret_start("A", scale, 1), 12, notes_per_string=3, title="A Pentatonic Minor \u2014 Shape 1")
    ds2 = _make_data("A", scale, projector.degree_fret_start("A", scale, 2), 12, notes_per_string=3, title="A Pentatonic Minor \u2014 Shape 2")
    diagrams = [ds1, ds2]
    result = multi_renderer.render(diagrams)
    assert "Shape 1" in result
    assert "Shape 2" in result
    # Both titles should appear as title-specific <text> elements (font-size="16")
    assert result.count('font-size="16"') == 2


def test_save_pdf_single_with_title(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    scale = catalog.get("pentatonic_minor")
    data = _make_data("A", scale, 0, 12, title="A Pentatonic Minor")
    out = tmp_path / "titled.pdf"
    raw = svg_renderer.render(data.cells, data.fret_start, data.fret_end)
    svg = svg_post_processor.process(raw, data.title)
    pdf_bytes = pdf_converter.svg_to_pdf(svg)
    file_writer.write_bytes(str(out), pdf_bytes)
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")


def test_save_multi_pdf_paginated_5_diagrams(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    scale = catalog.get("pentatonic_minor")
    diagrams = []
    for deg in range(1, 6):
        fs = projector.degree_fret_start("A", scale, deg)
        diagrams.append(_make_data("A", scale, fs, 12, notes_per_string=3, title=f"A Pentatonic Minor \u2014 Shape {deg}"))

    out = tmp_path / "multi.pdf"
    pdf_bytes = pdf_builder.build(diagrams)
    file_writer.write_bytes(str(out), pdf_bytes)
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")

    reader = PdfReader(str(out))
    # 5 diagrams with max_per_page=3 \u2192 2 pages
    assert len(reader.pages) == 2


def test_render_svg_title_inside_svg_root():
    scale = catalog.get("pentatonic_minor")
    data = _make_data("A", scale, 0, 12, title="A Pentatonic Minor")
    raw = svg_renderer.render(data.cells, data.fret_start, data.fret_end)
    svg = svg_post_processor.process(raw, data.title)
    svg_open_end = svg.index(">", svg.index("<svg")) + 1
    svg_close_start = svg.rindex("</svg>")
    inner = svg[svg_open_end:svg_close_start]
    assert "<text" in inner, "Title <text> must be inside <svg> root element"


def test_render_multi_svg_titles_inside_nested_svgs():
    scale = catalog.get("pentatonic_minor")
    ds1 = _make_data("A", scale, projector.degree_fret_start("A", scale, 1), 12, notes_per_string=3, title="Shape 1")
    ds2 = _make_data("A", scale, projector.degree_fret_start("A", scale, 2), 12, notes_per_string=3, title="Shape 2")
    diagrams = [ds1, ds2]
    result = multi_renderer.render(diagrams)

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
        assert diagrams[i].title in inner


def test_save_multi_pdf_7_diagrams(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    scale = catalog.get("major")
    diagrams = []
    for deg in range(1, 8):
        fs = projector.degree_fret_start("C", scale, deg)
        diagrams.append(_make_data("C", scale, fs, 12, notes_per_string=3, title=f"C Major \u2014 Shape {deg}"))

    out = tmp_path / "multi.pdf"
    pdf_bytes = pdf_builder.build(diagrams)
    file_writer.write_bytes(str(out), pdf_bytes)
    assert out.exists()

    reader = PdfReader(str(out))
    # 7 diagrams with max_per_page=3 \u2192 3 pages
    assert len(reader.pages) == 3


def _cairo_available() -> bool:
    """Check if cairosvg can actually be imported (native lib present)."""
    try:
        import cairosvg  # noqa: F401
        return True
    except (ImportError, OSError):
        return False

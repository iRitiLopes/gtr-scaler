"""SVG (and PDF) fretboard renderer using the fretboard library."""

# attrdict / pyyaml shipped with fretboard==1.0.0 use removed collections APIs.
# Patch before importing so they resolve correctly on Python 3.10+.
import collections
import collections.abc

for _name in ("Mapping", "MutableMapping", "Sequence", "Hashable"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))

import re
from io import StringIO
from pathlib import Path

from fretboard.fretboard import Fretboard as _Fretboard

from gtr_scaler.domain.fretboard import FretCell, project_scale, project_scale_n_notes
from gtr_scaler.domain.scales import Scale

# Shared interval → display label (same as ASCII renderer)
_INTERVAL_LABEL: dict[str, str] = {
    "1": "R",
    "m2": "b2",
    "M2": "2",
    "m3": "b3",
    "M3": "3",
    "P4": "4",
    "A4": "#4",
    "d5": "b5",
    "P5": "5",
    "m6": "b6",
    "M6": "6",
    "m7": "b7",
    "M7": "7",
}

_TETRAD_INTERVALS = frozenset({"1", "m3", "M3", "d5", "A4", "P5", "m7", "M7"})

# Colors matching the ASCII renderer's semantic coloring
_COLOR_ROOT = "firebrick"
_COLOR_TETRAD = "steelblue"
_COLOR_PASSING = "olivedrab"
_MULTI_DIAGRAM_GAP = 20  # px gap between stacked diagrams
_TITLE_HEIGHT = 60


def _interval_color(interval: str) -> str:
    if interval == "1":
        return _COLOR_ROOT
    if interval in _TETRAD_INTERVALS:
        return _COLOR_TETRAD
    return _COLOR_PASSING


def _fretboard_style(num_frets: int) -> dict[str, dict[str, int]]:
    """Return a style dict that scales the diagram height to fit all frets comfortably."""
    fret_space = 44  # px between frets — comfortable for radius-12 markers
    nut_size = 10
    v_padding = 60  # top + bottom margins (spacing * 2)
    height = fret_space * (num_frets - 1) + nut_size * 2 + v_padding
    return {
        "drawing": {
            "height": max(height, 180),
            "width": 280,
            "spacing": 30,
        },
        "marker": {
            "radius": 14,
            "font_size": 11,
        },
    }


def _build_fretboard(
    root: str,
    scale: Scale,
    cells: list[FretCell],
    fret_start: int,
    fret_end: int,
) -> _Fretboard:
    """Construct a Fretboard diagram object from pre-computed cells."""
    num_frets = fret_end - fret_start + 1
    style = _fretboard_style(num_frets + 1)  # +1 for the extra "phantom" row the library needs

    fb = _Fretboard(
        strings=6,
        frets=(fret_start, fret_end),
        style=style,
    )

    # String labels: low E → high e (left to right in the diagram)
    for string_idx, name in enumerate(("E", "A", "D", "G", "B", "e")):
        fb.add_string_label(string=string_idx, label=name, font_color="dimgray")

    for cell in cells:
        label = _INTERVAL_LABEL.get(cell.interval, "?")
        fb.add_marker(
            string=cell.string_idx,
            fret=cell.fret,
            label=label,
            color=_interval_color(cell.interval),
            font_color="white",
        )

    return fb


def _rotate_ccw(svg: str) -> str:
    """Rotate SVG content 90° counter-clockwise (portrait → landscape).

    A point (x, y) in the original maps to (y, W-x) in the rotated canvas,
    achieved with: transform="translate(0,W) rotate(-90)"
    The canvas dimensions are swapped: new width=H, new height=W.
    """
    m_w = re.search(r'<svg[^>]*\swidth="([^"]+)"', svg)
    m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
    assert m_w is not None, "SVG missing width attribute"
    assert m_h is not None, "SVG missing height attribute"
    w = float(m_w.group(1))
    h = float(m_h.group(1))

    svg = re.sub(r'(<svg[^>]*\s)width="[^"]+"', rf'\g<1>width="{h:.0f}"', svg, count=1)
    svg = re.sub(r'(<svg[^>]*\s)height="[^"]+"', rf'\g<1>height="{w:.0f}"', svg, count=1)

    # Wrap everything between <svg ...> and </svg> in a rotated group
    # (skip past the XML declaration to find the <svg> opening tag)
    svg_tag_start = svg.index("<svg")
    open_end = svg.index(">", svg_tag_start) + 1
    close_start = svg.rindex("</svg>")
    content = svg[open_end:close_start]
    wrapped = f'<g transform="translate(0,{w:.0f}) rotate(-90)">{content}</g>'
    return svg[:open_end] + wrapped + svg[close_start:]


def _wrap_with_title(
    svg: str, title: str, title_height: int = _TITLE_HEIGHT
) -> str:
    """Wrap an already-rotated SVG diagram with a title above it.

    The input SVG is assumed to already be rotated 90° CCW (via _rotate_ccw).
    Its structure is: <svg width="H" height="280">
                        <g transform="translate(0,280) rotate(-90)">...</g>
                      </svg>

    This function:
      1. Increases the SVG height by title_height.
      2. Shifts the inner <g> transform's Y translation by the same amount.
      3. Inserts a centered <text> element before the <g>.
    """
    m_w = re.search(r'<svg[^>]*\swidth="([^"]+)"', svg)
    m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
    assert m_w is not None, "SVG missing width attribute"
    assert m_h is not None, "SVG missing height attribute"
    w = float(m_w.group(1))
    h = float(m_h.group(1))
    new_height = h + title_height

    # Update height
    svg = re.sub(
        r'(<svg[^>]*\s)height="[^"]+"',
        rf'\g<1>height="{new_height:.0f}"',
        svg,
        count=1,
    )

    # Shift the <g> transform's Y translation
    def _shift_g(match: re.Match[str]) -> str:
        old_y = float(match.group(1))
        new_y = old_y + title_height
        return f'translate(0,{new_y:.0f}) rotate(-90)'

    svg = re.sub(
        r'translate\(0,([^)]+)\)\s*rotate\(-90\)',
        _shift_g,
        svg,
        count=1,
    )

    # Insert title text after <svg ...>
    text_elem = (
        f'<text x="{w / 2:.0f}" y="{title_height / 2 + 7:.0f}" '
        f'text-anchor="middle" font-family="sans-serif" '
        f'font-size="16" font-weight="bold" fill="#333">'
        f"{title}</text>\n"
    )
    svg_tag_start = svg.index("<svg")
    svg_tag_end = svg.index(">", svg_tag_start) + 1
    svg = svg[:svg_tag_end] + "\n" + text_elem + svg[svg_tag_end:]

    return svg


def render_svg(
    root: str,
    scale: Scale,
    fret_start: int = 0,
    fret_end: int = 12,
    notes_per_string: int | None = None,
    title: str | None = None,
) -> str:
    """Return an SVG string of the fretboard diagram."""
    if notes_per_string is not None:
        cells, fret_end = project_scale_n_notes(root, scale, notes_per_string, fret_start)
    else:
        cells = project_scale(root, scale, fret_start, fret_end)

    fb = _build_fretboard(root, scale, cells, fret_start, fret_end)
    fb.draw()

    buf = StringIO()
    fb.drawing.write(buf)
    svg = _rotate_ccw(buf.getvalue())
    if title is not None:
        svg = _wrap_with_title(svg, title)
    return svg


def save_svg(
    path: str | Path,
    root: str,
    scale: Scale,
    fret_start: int = 0,
    fret_end: int = 12,
    notes_per_string: int | None = None,
    title: str | None = None,
) -> None:
    """Save the fretboard diagram as an SVG file."""
    svg = render_svg(root, scale, fret_start, fret_end, notes_per_string, title=title)
    Path(path).write_text(svg, encoding="utf-8")


def save_pdf(
    path: str | Path,
    root: str,
    scale: Scale,
    fret_start: int = 0,
    fret_end: int = 12,
    notes_per_string: int | None = None,
    title: str | None = None,
) -> None:
    """Save the fretboard diagram as a PDF file (via cairosvg)."""
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError("cairosvg is required for PDF export: pip install cairosvg") from exc

    svg = render_svg(root, scale, fret_start, fret_end, notes_per_string, title=title)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(path))


def render_multi_svg(
    diagrams: list[tuple[str, Scale, int, int, int | None]],
    titles: list[str] | None = None,
) -> str:
    """Stack multiple fretboard diagrams vertically into a single SVG."""
    if not diagrams:
        raise ValueError("diagrams list must not be empty")
    if titles is not None and len(titles) != len(diagrams):
        raise ValueError(
            f"titles length ({len(titles)}) must match diagrams length ({len(diagrams)})"
        )

    parts: list[str] = []
    total_height = 0
    max_width = 0

    for i, (root, scale, fret_start, fret_end, notes_per_string) in enumerate(diagrams):
        title = titles[i] if titles else None
        svg = render_svg(root, scale, fret_start, fret_end, notes_per_string, title=title)
        m_w = re.search(r'<svg[^>]*\swidth="([^"]+)"', svg)
        m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
        assert m_w is not None and m_h is not None, "SVG missing width/height"
        w = int(float(m_w.group(1)))
        h = int(float(m_h.group(1)))
        max_width = max(max_width, w)
        offset = total_height
        total_height += h
        if i < len(diagrams) - 1:
            total_height += _MULTI_DIAGRAM_GAP

        # Strip XML declaration
        svg = re.sub(r'<\?xml[^?]*\?>\s*', '', svg)
        # Inject x/y offset into the outer <svg> tag so it acts as a nested viewport
        svg = re.sub(r'(<svg)(\s)', rf'\1 x="0" y="{offset}"\2', svg, count=1)
        parts.append(svg)

    master = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{max_width}" height="{total_height}">\n'
        + "\n".join(parts)
        + "\n</svg>"
    )
    return master


def save_multi_svg(
    path: str | Path,
    diagrams: list[tuple[str, Scale, int, int, int | None]],
    titles: list[str] | None = None,
) -> None:
    """Save multiple diagrams as a single stacked SVG file."""
    svg = render_multi_svg(diagrams, titles=titles)
    Path(path).write_text(svg, encoding="utf-8")


def save_multi_pdf(
    path: str | Path,
    diagrams: list[tuple[str, Scale, int, int, int | None]],
    titles: list[str] | None = None,
    max_per_page: int = 3,
) -> None:
    """Save multiple diagrams as a paginated PDF file.

    Diagrams are split into chunks of ``max_per_page`` per page.
    Each chunk is rendered as a single SVG, converted to PDF via cairosvg,
    then all pages are merged with pypdf.
    """
    if titles is not None and len(titles) != len(diagrams):
        raise ValueError(
            f"titles length ({len(titles)}) must match "
            f"diagrams length ({len(diagrams)})"
        )

    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError(
            "cairosvg is required for PDF export: pip install cairosvg"
        ) from exc

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required for multi-page PDF export: pip install pypdf"
        ) from exc

    from io import BytesIO

    # Split into chunks
    page_bytes_list: list[bytes] = []
    for start in range(0, len(diagrams), max_per_page):
        end = start + max_per_page
        chunk = diagrams[start:end]
        chunk_titles = titles[start:end] if titles else None
        page_svg = render_multi_svg(chunk, titles=chunk_titles)
        page_bytes = cairosvg.svg2pdf(bytestring=page_svg.encode())
        if page_bytes is None:
            # Older cairosvg may require write_to; use temp file
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name
            cairosvg.svg2pdf(bytestring=page_svg.encode(), write_to=tmp_path)
            page_bytes = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink()
        page_bytes_list.append(page_bytes)

    # Merge pages
    writer = PdfWriter()
    for page_data in page_bytes_list:
        reader = PdfReader(BytesIO(page_data))
        for page in reader.pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    Path(path).write_bytes(output.getvalue())

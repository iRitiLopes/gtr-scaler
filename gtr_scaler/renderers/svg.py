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
    "1":  "R",
    "m2": "b2", "M2": "2",
    "m3": "b3", "M3": "3",
    "P4": "4",  "A4": "#4",
    "d5": "b5", "P5": "5",
    "m6": "b6", "M6": "6",
    "m7": "b7", "M7": "7",
}

_TETRAD_INTERVALS = frozenset({"1", "m3", "M3", "d5", "A4", "P5", "m7", "M7"})

# Colors matching the ASCII renderer's semantic coloring
_COLOR_ROOT    = "firebrick"
_COLOR_TETRAD  = "steelblue"
_COLOR_PASSING = "olivedrab"


def _interval_color(interval: str) -> str:
    if interval == "1":
        return _COLOR_ROOT
    if interval in _TETRAD_INTERVALS:
        return _COLOR_TETRAD
    return _COLOR_PASSING


def _fretboard_style(num_frets: int) -> dict:
    """Return a style dict that scales the diagram height to fit all frets comfortably."""
    fret_space = 44          # px between frets — comfortable for radius-12 markers
    nut_size   = 10
    v_padding  = 60          # top + bottom margins (spacing * 2)
    height     = fret_space * (num_frets - 1) + nut_size * 2 + v_padding
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
    w = float(re.search(r'<svg[^>]*\swidth="([^"]+)"', svg).group(1))
    h = float(re.search(r'<svg[^>]*\sheight="([^"]+)"', svg).group(1))

    svg = re.sub(r'(<svg[^>]*\s)width="[^"]+"', rf'\g<1>width="{h:.0f}"', svg, count=1)
    svg = re.sub(r'(<svg[^>]*\s)height="[^"]+"', rf'\g<1>height="{w:.0f}"', svg, count=1)

    # Wrap everything between <svg ...> and </svg> in a rotated group
    # (skip past the XML declaration to find the <svg> opening tag)
    svg_tag_start = svg.index('<svg')
    open_end      = svg.index('>', svg_tag_start) + 1
    close_start   = svg.rindex('</svg>')
    content     = svg[open_end:close_start]
    wrapped     = f'<g transform="translate(0,{w:.0f}) rotate(-90)">{content}</g>'
    return svg[:open_end] + wrapped + svg[close_start:]


def render_svg(
    root: str,
    scale: Scale,
    fret_start: int = 0,
    fret_end: int = 12,
    notes_per_string: int | None = None,
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
    return _rotate_ccw(buf.getvalue())


def save_svg(
    path: str | Path,
    root: str,
    scale: Scale,
    fret_start: int = 0,
    fret_end: int = 12,
    notes_per_string: int | None = None,
) -> None:
    """Save the fretboard diagram as an SVG file."""
    svg = render_svg(root, scale, fret_start, fret_end, notes_per_string)
    Path(path).write_text(svg, encoding="utf-8")


def save_pdf(
    path: str | Path,
    root: str,
    scale: Scale,
    fret_start: int = 0,
    fret_end: int = 12,
    notes_per_string: int | None = None,
) -> None:
    """Save the fretboard diagram as a PDF file (via cairosvg)."""
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError(
            "cairosvg is required for PDF export: pip install cairosvg"
        ) from exc

    svg = render_svg(root, scale, fret_start, fret_end, notes_per_string)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(path))

"""SVG fretboard renderer using the fretboard library."""

# attrdict / pyyaml shipped with fretboard==1.0.0 use removed collections APIs.
# Patch before importing so they resolve correctly on Python 3.10+.
import collections
import collections.abc

for _name in ("Mapping", "MutableMapping", "Sequence", "Hashable"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))

import re
from io import StringIO
from xml.sax.saxutils import escape

from fretboard.fretboard import Fretboard as _Fretboard

from gtr_scaler.domain.fretboard import FretCell
from gtr_scaler.renderers._constants import _INTERVAL_LABEL, _TETRAD_INTERVALS

# Colors matching the ASCII renderer's semantic coloring
_COLOR_ROOT = "firebrick"
_COLOR_TETRAD = "steelblue"
_COLOR_PASSING = "olivedrab"
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


class SvgPostProcessor:
    """Applies rotation and title wrapping to raw fretboard SVG strings."""

    def process(self, svg: str, title: str | None = None) -> str:
        """Rotate 90° CCW and optionally prepend a title."""
        svg = self._rotate_ccw(svg)
        if title is not None:
            svg = self._wrap_with_title(svg, title)
        return svg

    @staticmethod
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

    @staticmethod
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
        escaped_title = escape(title)
        text_elem = (
            f'<text x="{w / 2:.0f}" y="{title_height / 2 + 7:.0f}" '
            f'text-anchor="middle" font-family="sans-serif" '
            f'font-size="16" font-weight="bold" fill="#333">'
            f"{escaped_title}</text>\n"
        )
        svg_tag_start = svg.index("<svg")
        svg_tag_end = svg.index(">", svg_tag_start) + 1
        svg = svg[:svg_tag_end] + "\n" + text_elem + svg[svg_tag_end:]

        return svg


class SvgRenderer:
    """Renders raw fretboard diagrams as SVG strings (no rotation, no title)."""

    def render(
        self,
        cells: list[FretCell],
        fret_start: int = 0,
        fret_end: int = 12,
    ) -> str:
        """Return a raw SVG string of the fretboard diagram."""
        fb = _build_fretboard(cells, fret_start, fret_end)
        fb.draw()

        buf = StringIO()
        fb.drawing.write(buf)
        return buf.getvalue()

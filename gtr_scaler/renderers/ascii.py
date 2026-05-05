"""ASCII fretboard renderer."""

import sys

from gtr_scaler.domain.fretboard import STRING_NAMES, FretboardProjector, FretCell
from gtr_scaler.domain.scales import Scale
from gtr_scaler.renderers._constants import _INTERVAL_LABEL, _TETRAD_INTERVALS

_RESET = "\033[0m"
_RED = "\033[1;91m"  # bold bright red   — root
_GREEN = "\033[1;92m"  # bold bright green — tetrad tones
_YELLOW = "\033[0;33m"  # yellow            — passing tones


def _colorize(text: str, interval: str, color: bool) -> str:
    if not color:
        return text
    if interval == "1":
        code = _RED
    elif interval in _TETRAD_INTERVALS:
        code = _GREEN
    else:
        code = _YELLOW
    return f"{code}{text}{_RESET}"


def _marker(cell: FretCell, color: bool) -> str:
    """Return the padded cell string (dashes + label) between fret bars."""
    label = _INTERVAL_LABEL.get(cell.interval, "?")
    colored_label = _colorize(label, cell.interval, color)
    # Pad with dashes so visual width is always 4 chars (label is 1 or 2 visible chars)
    pad = "-" * (3 - len(label))
    return f"-{colored_label}{pad}"


class AsciiRenderer:
    """Renders fretboard diagrams as ASCII art for terminal display."""

    def __init__(self, projector: FretboardProjector, color: bool | None = None) -> None:
        self._projector = projector
        self._color = color

    def render(
        self,
        root: str,
        scale: Scale,
        fret_start: int = 0,
        fret_end: int = 12,
        notes_per_string: int | None = None,
        title: str | None = None,
        color: bool | None = None,
    ) -> str:
        """Return a multi-line ASCII fretboard diagram string.

        color: True=always, False=never, None=auto-detect (tty).
               If not provided here, uses the constructor default.
        notes_per_string: if set, show exactly this many scale notes per string and
                          ignore fret_end (the diagram ends at the last note needed).
        title: optional title string for the header line.
        """
        # Resolve color: explicit arg > constructor default > auto-detect
        if color is None:
            color = self._color
        if color is None:
            color = sys.stdout.isatty()

        if notes_per_string is not None:
            cells, fret_end = self._projector.project_n_notes(
                root, scale, notes_per_string, fret_start
            )
        else:
            cells = self._projector.project(root, scale, fret_start, fret_end)
        cell_map: dict[tuple[int, int], FretCell] = {(c.string_idx, c.fret): c for c in cells}

        lines: list[str] = []
        if title is not None:
            title_str = title
        else:
            title_str = f"{root} {scale.display_name}"
        lines.append(f"{title_str}  |  Standard tuning (E A D G B e)")
        lines.append("")

        # Fret number header
        header = "   " + "".join(f"{f:5}" for f in range(fret_start, fret_end + 1))
        lines.append(header)

        # Strings from high e (idx 5) down to low E (idx 0)
        for string_idx in range(5, -1, -1):
            name = STRING_NAMES[string_idx]
            row_parts: list[str] = [f"{name:2} |"]
            for fret in range(fret_start, fret_end + 1):
                cell = cell_map.get((string_idx, fret))
                row_parts.append(f"{_marker(cell, color) if cell else '----'}|")
            lines.append("".join(row_parts))

        # Legend — color the labels to match the diagram
        seen_intervals = {c.interval for c in cells}
        legend_parts = []
        for symbol, label in _INTERVAL_LABEL.items():
            if symbol in seen_intervals:
                colored = _colorize(label, symbol, color)
                legend_parts.append(f"{colored}={symbol}")
        lines.append("")
        lines.append("  " + "   ".join(legend_parts))
        return "\n".join(lines)

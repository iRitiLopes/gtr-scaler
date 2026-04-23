"""ASCII fretboard renderer."""

import sys

from gtr_scaler.domain.fretboard import FretCell, STRING_NAMES, project_scale, project_scale_n_notes
from gtr_scaler.domain.scales import Scale

# Interval symbol → display label (1 or 2 chars)
_INTERVAL_LABEL: dict[str, str] = {
    '1':  'R',
    'm2': 'b2', 'M2': '2',
    'm3': 'b3', 'M3': '3',
    'P4': '4',  'A4': '#4',
    'd5': 'b5', 'P5': '5',
    'm6': 'b6', 'M6': '6',
    'm7': 'b7', 'M7': '7',
}

# Tetrad intervals (root, 3rd, 5th, 7th)
_TETRAD_INTERVALS = frozenset({'1', 'm3', 'M3', 'd5', 'A4', 'P5', 'm7', 'M7'})

_RESET  = '\033[0m'
_RED    = '\033[1;91m'   # bold bright red   — root
_GREEN  = '\033[1;92m'   # bold bright green — tetrad tones
_YELLOW = '\033[0;33m'   # yellow            — passing tones


def _colorize(text: str, interval: str, color: bool) -> str:
    if not color:
        return text
    if interval == '1':
        code = _RED
    elif interval in _TETRAD_INTERVALS:
        code = _GREEN
    else:
        code = _YELLOW
    return f"{code}{text}{_RESET}"


def _marker(cell: FretCell, color: bool) -> str:
    """Return the padded cell string (dashes + label) between fret bars."""
    label = _INTERVAL_LABEL.get(cell.interval, '?')
    colored_label = _colorize(label, cell.interval, color)
    # Pad with dashes so visual width is always 4 chars (label is 1 or 2 visible chars)
    pad = '-' * (3 - len(label))
    return f"-{colored_label}{pad}"


def render(
    root: str, scale: Scale,
    fret_start: int = 0, fret_end: int = 12,
    color: bool | None = None,
    notes_per_string: int | None = None,
) -> str:
    """Return a multi-line ASCII fretboard diagram string.

    color: True=always, False=never, None=auto-detect (tty).
    notes_per_string: if set, show exactly this many scale notes per string and
                      ignore fret_end (the diagram ends at the last note needed).
    """
    if color is None:
        color = sys.stdout.isatty()

    if notes_per_string is not None:
        cells, fret_end = project_scale_n_notes(root, scale, notes_per_string, fret_start)
    else:
        cells = project_scale(root, scale, fret_start, fret_end)
    cell_map: dict[tuple[int, int], FretCell] = {(c.string_idx, c.fret): c for c in cells}

    lines: list[str] = []
    lines.append(f"{root} {scale.display_name}  |  Standard tuning (E A D G B e)")
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

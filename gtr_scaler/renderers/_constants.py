"""Shared constants for fretboard renderers."""

# Interval symbol → display label (1 or 2 chars)
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

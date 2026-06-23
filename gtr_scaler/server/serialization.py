"""JSON serialization helpers for domain objects."""

from __future__ import annotations

from gtr_scaler.domain.fretboard import FretCell
from gtr_scaler.domain.scales import Scale
from gtr_scaler.renderers._constants import _INTERVAL_LABEL


def serialize_fret_cell(cell: FretCell) -> dict[str, object]:
    """Serialize a single :class:`FretCell` to a JSON-friendly dict."""
    return {
        "string_idx": cell.string_idx,
        "fret": cell.fret,
        "interval": cell.interval,
        "label": _INTERVAL_LABEL.get(cell.interval, "?"),
        "is_root": cell.is_root,
    }


def serialize_scale(scale: Scale) -> dict[str, object]:
    """Serialize a :class:`Scale` to a JSON-friendly dict."""
    return {
        "name": scale.name,
        "display_name": scale.display_name,
        "intervals": list(scale.intervals),
        "num_notes": len(scale.intervals),
    }


def serialize_diagram_data(
    root: str,
    scale: Scale,
    mode: int,
    start_degree: int,
    fret_start: int,
    fret_end: int,
    nps: int | None,
    cells: list[FretCell],
) -> dict[str, object]:
    """Build the full JSON response for a scale diagram query."""
    seen_intervals = {c.interval for c in cells}
    interval_labels = {
        sym: _INTERVAL_LABEL[sym]
        for sym in scale.intervals
        if sym in seen_intervals
    }

    return {
        "root": root,
        "scale": serialize_scale(scale),
        "mode": mode,
        "start_degree": start_degree,
        "fret_start": fret_start,
        "fret_end": fret_end,
        "notes_per_string": nps,
        "interval_labels": interval_labels,
        "cells": [serialize_fret_cell(c) for c in cells],
    }

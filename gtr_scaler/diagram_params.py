"""Shared diagram parameter dataclasses used by CLI, web, and engine."""

from __future__ import annotations

from dataclasses import dataclass

from gtr_scaler.domain.scales import Scale


@dataclass(frozen=True)
class DiagramParams:
    """Validated, resolved parameters ready for rendering."""

    root: str
    scale_name: str
    scale: Scale
    mode: int
    start_degree: int
    frets: str
    nps: int | None
    all_degrees: bool
    effective_root: str
    effective_scale: Scale


@dataclass(frozen=True)
class DiagramData:
    """Projected fretboard cells and metadata for a single diagram."""

    cells: list[object]  # list[FretCell] — declared as object to avoid circular import
    fret_start: int
    fret_end: int
    title: str

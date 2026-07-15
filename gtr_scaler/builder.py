"""Diagram builder — pure projection from parameters to cells."""

from __future__ import annotations

from gtr_scaler.diagram_params import DiagramParams
from gtr_scaler.domain.fretboard import FretCell, FretboardProjector


class DiagramBuilder:
    """Projects a :class:`DiagramParams` to raw fretboard cells.

    No rendering, no titles — just the geometry.
    """

    def __init__(self, projector: FretboardProjector) -> None:
        self._projector = projector

    @staticmethod
    def _parse_frets(value: str) -> tuple[int, int]:
        """Accept ``'22'`` → ``(0, 22)`` or ``'5-9'`` → ``(5, 9)``."""
        if "-" in value:
            parts = value.split("-", 1)
            start, end = int(parts[0]), int(parts[1])
            if start < 0 or end < start:
                raise ValueError(
                    f"Invalid fret range {value!r}: need start >= 0 and end >= start"
                )
            return start, end
        n = int(value)
        if n < 0:
            raise ValueError(f"Frets must be >= 0, got {n}")
        return 0, n

    def _compute_fret_start(self, params: DiagramParams) -> int:
        """Mirror of the old ``GtrScalerApp._get_render_params`` / ``compute_fret_start``."""
        if params.nps is not None:
            return self._projector.degree_fret_start_with_shift(
                params.effective_root,
                params.effective_scale,
                params.start_degree,
                params.nps,
            )
        base_start, _fret_end = self._parse_frets(params.frets)
        if params.start_degree != 1:
            return self._projector.degree_fret_start(
                params.effective_root,
                params.effective_scale,
                params.start_degree,
            )
        return base_start

    def build(self, params: DiagramParams) -> tuple[list[FretCell], int, int]:
        """Return ``(cells, fret_start, fret_end)`` for the given parameters."""
        fret_start = self._compute_fret_start(params)

        if params.nps is not None:
            cells, fret_end = self._projector.project_n_notes(
                params.effective_root,
                params.effective_scale,
                params.nps,
                fret_start,
            )
        else:
            _base_start, fret_end = self._parse_frets(params.frets)
            if params.start_degree != 1:
                fret_start = self._projector.degree_fret_start(
                    params.effective_root,
                    params.effective_scale,
                    params.start_degree,
                )
            cells = self._projector.project(
                params.effective_root,
                params.effective_scale,
                fret_start,
                fret_end,
            )

        return cells, fret_start, fret_end

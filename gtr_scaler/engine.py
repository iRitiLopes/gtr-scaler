"""Diagram orchestration engine — thin wrapper over :class:`DiagramBuilder`."""

from __future__ import annotations

from dataclasses import replace

from gtr_scaler.builder import DiagramBuilder
from gtr_scaler.diagram_params import DiagramData, DiagramParams


class DiagramEngine:
    """Builds :class:`DiagramData` from :class:`DiagramParams`.

    Absorbs the duplication that previously lived in ``GtrScalerApp.run()``,
    Flask route handlers, and ``server/validation.compute_fret_start``.
    """

    def __init__(self, builder: DiagramBuilder) -> None:
        self._builder = builder

    def build_single(self, params: DiagramParams) -> DiagramData:
        """Return a single :class:`DiagramData` for the given parameters."""
        if params.all_degrees:
            raise ValueError(
                "build_single does not support all_degrees; use build_all_degrees"
            )

        cells, fret_start, fret_end = self._builder.build(params)
        title = f"{params.effective_root} {params.effective_scale.display_name}"
        return DiagramData(
            cells=cells, fret_start=fret_start, fret_end=fret_end, title=title
        )

    def build_all_degrees(self, params: DiagramParams) -> list[DiagramData]:
        """Return one :class:`DiagramData` per scale degree (CAGED-style shapes)."""
        if not params.all_degrees:
            raise ValueError("build_all_degrees requires all_degrees=True")
        if params.nps is None or not 2 <= params.nps <= 4:
            raise ValueError(
                "all_degrees requires nps with a value between 2 and 4"
            )
        if params.start_degree != 1:
            raise ValueError("all_degrees cannot be used with start_degree")

        result: list[DiagramData] = []
        for deg in range(1, len(params.effective_scale.intervals) + 1):
            degree_params = replace(params, start_degree=deg)
            cells, fs, fe = self._builder.build(degree_params)
            title = (
                f"{params.effective_root} {params.effective_scale.display_name}"
                f" \u2014 Shape {deg}"
            )
            result.append(
                DiagramData(cells=cells, fret_start=fs, fret_end=fe, title=title)
            )
        return result

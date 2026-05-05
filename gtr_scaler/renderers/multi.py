"""Multi-diagram SVG renderer — stacks individual diagrams vertically."""

import re
from dataclasses import dataclass

from gtr_scaler.domain.scales import Scale
from gtr_scaler.renderers.svg import SvgRenderer


@dataclass(frozen=True)
class DiagramSpec:
    root: str
    scale: Scale
    fret_start: int
    fret_end: int
    notes_per_string: int | None = None


class MultiDiagramRenderer:
    """Stacks multiple fretboard diagrams vertically into a single SVG."""

    def __init__(self, svg_renderer: SvgRenderer, gap: int = 20) -> None:
        self._svg_renderer = svg_renderer
        self._gap = gap

    def render(
        self,
        diagrams: list[DiagramSpec],
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

        for i, spec in enumerate(diagrams):
            title = titles[i] if titles else None
            svg = self._svg_renderer.render(
                spec.root,
                spec.scale,
                spec.fret_start,
                spec.fret_end,
                notes_per_string=spec.notes_per_string,
                title=title,
            )
            m_w = re.search(r'<svg[^>]*\swidth="([^"]+)"', svg)
            m_h = re.search(r'<svg[^>]*\sheight="([^"]+)"', svg)
            assert m_w is not None and m_h is not None, "SVG missing width/height"
            w = int(float(m_w.group(1)))
            h = int(float(m_h.group(1)))
            max_width = max(max_width, w)
            offset = total_height
            total_height += h
            if i < len(diagrams) - 1:
                total_height += self._gap

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

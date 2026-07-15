"""Multi-diagram SVG renderer — stacks individual diagrams vertically."""

import re

from gtr_scaler.diagram_params import DiagramData
from gtr_scaler.renderers.svg import SvgPostProcessor, SvgRenderer


class MultiDiagramRenderer:
    """Stacks multiple fretboard diagrams vertically into a single SVG."""

    def __init__(
        self,
        svg_renderer: SvgRenderer,
        post_processor: SvgPostProcessor,
        gap: int = 20,
    ) -> None:
        self._svg_renderer = svg_renderer
        self._post_processor = post_processor
        self._gap = gap

    def render(self, diagrams: list[DiagramData]) -> str:
        """Stack multiple fretboard diagrams vertically into a single SVG."""
        if not diagrams:
            raise ValueError("diagrams list must not be empty")

        parts: list[str] = []
        total_height = 0
        max_width = 0

        for i, data in enumerate(diagrams):
            raw = self._svg_renderer.render(
                data.cells,
                data.fret_start,
                data.fret_end,
            )
            svg = self._post_processor.process(raw, data.title)
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

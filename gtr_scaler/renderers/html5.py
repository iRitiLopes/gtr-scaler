"""HTML5 fretboard renderer — self-contained CSS/JS/HTML fragments."""

from __future__ import annotations

import html

from gtr_scaler.domain.fretboard import STRING_NAMES, FretCell
from gtr_scaler.renderers._constants import _INTERVAL_LABEL, _TETRAD_INTERVALS

# Full interval names for tooltips
_INTERVAL_FULL_NAME: dict[str, str] = {
    "1": "Root",
    "m2": "Minor 2nd",
    "M2": "Major 2nd",
    "m3": "Minor 3rd",
    "M3": "Major 3rd",
    "P4": "Perfect 4th",
    "A4": "Augmented 4th",
    "d5": "Diminished 5th",
    "P5": "Perfect 5th",
    "m6": "Minor 6th",
    "M6": "Major 6th",
    "m7": "Minor 7th",
    "M7": "Major 7th",
}


def _interval_color_class(interval: str) -> str:
    """Return the CSS modifier class for a given interval symbol."""
    if interval == "1":
        return "gtr-marker--root"
    if interval in _TETRAD_INTERVALS:
        return "gtr-marker--tetrad"
    return "gtr-marker--passing"


class Html5Renderer:
    """Renders fretboard diagrams as self-contained HTML fragments."""

    def render(
        self,
        cells: list[FretCell],
        fret_start: int,
        fret_end: int,
        title: str | None = None,
    ) -> str:
        """Return a self-contained HTML fragment string."""
        cell_map: dict[tuple[int, int], FretCell] = {(c.string_idx, c.fret): c for c in cells}
        num_frets = fret_end - fret_start + 1

        parts: list[str] = []
        parts.append(self._build_css(num_frets))

        diagram_title = title or ""
        escaped_title = html.escape(diagram_title)

        parts.append('<div class="gtr-diagram">')
        parts.append(f"<h4>{escaped_title}</h4>")
        parts.append(self._build_fretboard_html(cell_map, fret_start, fret_end))
        parts.append(self._build_legend_html(cells))
        parts.append("</div>")
        parts.append(self._build_js())

        return "\n".join(parts)

    def _build_css(self, num_frets: int) -> str:
        """Return a <style> block with CSS grid layout for the fretboard."""
        return f"""<style>
.gtr-diagram {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  margin: 1rem 0;
}}
.gtr-diagram h4 {{
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #333;
}}
.gtr-fretboard-wrap {{
  overflow-x: auto;
}}
.gtr-fretboard {{
  display: grid;
  grid-template-columns: 32px repeat({num_frets}, 50px);
  grid-template-rows: 28px repeat(6, 40px);
  gap: 0;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  width: fit-content;
}}
.gtr-label {{
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: #555;
  border-right: 2px solid #888;
}}
.gtr-fret-num {{
  display: flex;
  align-items: flex-end;
  justify-content: center;
  font-size: 0.7rem;
  color: #777;
  padding-bottom: 2px;
}}
.gtr-cell {{
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #ccc;
  border-bottom: 1px solid #eee;
  position: relative;
}}
.gtr-cell:first-child {{
  border-bottom: none;
}}
.gtr-string-row .gtr-cell {{
  border-bottom: none;
}}
.gtr-nut {{
  border-left: 3px solid #333;
}}
.gtr-marker {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: default;
  user-select: none;
  transition: transform 0.15s ease;
}}
.gtr-marker:hover {{
  transform: scale(1.25);
}}
.gtr-marker--root {{
  background: #B22222;
}}
.gtr-marker--tetrad {{
  background: #4682B4;
}}
.gtr-marker--passing {{
  background: #6B8E23;
}}
.gtr-legend {{
  margin-top: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: #555;
}}
.gtr-legend-item {{
  display: flex;
  align-items: center;
  gap: 4px;
}}
.gtr-legend-dot {{
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}}
#gtr-tooltip {{
  position: fixed;
  pointer-events: none;
  background: #333;
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  z-index: 9999;
  white-space: nowrap;
  display: none;
}}
</style>"""

    def _build_js(self) -> str:
        """Return a <script> block with vanilla JS tooltip logic."""
        return """<script>
(function() {
  "use strict";
  if (document.getElementById("gtr-tooltip")) return;
  var tooltip = null;

  function getTooltip() {
    if (!tooltip) {
      tooltip = document.createElement("div");
      tooltip.id = "gtr-tooltip";
      document.body.appendChild(tooltip);
    }
    return tooltip;
  }

  document.addEventListener("mouseenter", function(e) {
    var marker = e.target.closest(".gtr-marker");
    if (!marker) return;
    var tip = getTooltip();
    tip.textContent = marker.getAttribute("data-interval-full") || "";
    tip.style.display = "block";
  }, true);

  document.addEventListener("mousemove", function(e) {
    var marker = e.target.closest(".gtr-marker");
    if (!marker) return;
    var tip = getTooltip();
    tip.style.left = (e.clientX + 12) + "px";
    tip.style.top = (e.clientY - 30) + "px";
  }, true);

  document.addEventListener("mouseleave", function(e) {
    var marker = e.target.closest(".gtr-marker");
    if (!marker) return;
    var tip = getTooltip();
    tip.style.display = "none";
  }, true);
})();
</script>"""

    def _build_fretboard_html(
        self,
        cell_map: dict[tuple[int, int], FretCell],
        fret_start: int,
        fret_end: int,
    ) -> str:
        """Return the CSS-grid-based fretboard HTML."""
        frets = range(fret_start, fret_end + 1)
        num_frets = fret_end - fret_start + 1

        lines: list[str] = []
        lines.append('<div class="gtr-fretboard-wrap">')
        lines.append(
            f'<div class="gtr-fretboard" style="'
            f"grid-template-columns: 32px repeat({num_frets}, 50px);\">"
        )

        # Header row: empty label cell + fret numbers
        lines.append('<div class="gtr-label"></div>')
        for fret in frets:
            lines.append(f'<div class="gtr-fret-num">{fret}</div>')

        # String rows: high e (idx 5) down to low E (idx 0)
        for string_idx in range(5, -1, -1):
            name = STRING_NAMES[string_idx]

            lines.append(f'<div class="gtr-label">{name}</div>')
            for fret in frets:
                cell = cell_map.get((string_idx, fret))
                nut_class = " gtr-nut" if fret == fret_start else ""
                if cell:
                    label = _INTERVAL_LABEL.get(cell.interval, "?")
                    color_class = _interval_color_class(cell.interval)
                    full_name = _INTERVAL_FULL_NAME.get(cell.interval, cell.interval)
                    escaped_full = html.escape(full_name)
                    lines.append(
                        f'<div class="gtr-cell{nut_class}">'
                        f'<span class="gtr-marker {color_class}" '
                        f'data-interval-full="{escaped_full}">'
                        f"{label}</span></div>"
                    )
                else:
                    lines.append(f'<div class="gtr-cell{nut_class}"></div>')

        lines.append("</div>")  # .gtr-fretboard
        lines.append("</div>")  # .gtr-fretboard-wrap
        return "\n".join(lines)

    def _build_legend_html(self, cells: list[FretCell]) -> str:
        """Return a legend div with colored dots for each present interval."""
        seen = {c.interval for c in cells}
        parts: list[str] = ['<div class="gtr-legend">']
        for symbol, label in _INTERVAL_LABEL.items():
            if symbol in seen:
                color_class = _interval_color_class(symbol)
                # Map CSS class to hex color for the legend dot
                if "root" in color_class:
                    dot_color = "#B22222"
                elif "tetrad" in color_class:
                    dot_color = "#4682B4"
                else:
                    dot_color = "#6B8E23"
                parts.append(
                    f'<span class="gtr-legend-item">'
                    f'<span class="gtr-legend-dot" style="background:{dot_color}"></span>'
                    f"{label}={symbol}</span>"
                )
        parts.append("</div>")
        return "\n".join(parts)

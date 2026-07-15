"""HTML frontend routes for the gtr-scaler web interface."""

from __future__ import annotations

import html as html_mod
import json

from flask import Blueprint, Response, current_app, render_template, request
from werkzeug.exceptions import HTTPException

from gtr_scaler.diagram_params import DiagramParams
from gtr_scaler.domain.scales import SCALE_PATTERNS
from gtr_scaler.server.validation import parse_diagram_params

pages_bp = Blueprint("pages", __name__)

_CHROMATIC_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_SCALE_COLORS: dict[str, str] = {
    "pentatonic_minor": "#e74c3c",
    "pentatonic_major": "#27ae60",
    "major": "#3498db",
    "ionian": "#2980b9",
    "dorian": "#e67e22",
    "phrygian": "#9b59b6",
    "lydian": "#1abc9c",
    "mixolydian": "#f39c12",
    "aeolian": "#e91e63",
    "locrian": "#607d8b",
    "natural_minor": "#795548",
    "harmonic_minor": "#8e44ad",
    "melodic_minor": "#16a085",
    "altered": "#c0392b",
    "blues": "#2c3e50",
}


def _get_scales() -> list[tuple[str, str]]:
    """Return list of ``(key, display_name)`` for the scale dropdown."""
    catalog = current_app.config["SCALE_CATALOG"]
    return [(name, catalog.get(name).display_name) for name in SCALE_PATTERNS]


def _get_scale_interval_counts() -> dict[str, int]:
    """Return a mapping of scale key → number of intervals for JS constraint logic."""
    catalog = current_app.config["SCALE_CATALOG"]
    return {name: len(catalog.get(name).intervals) for name in SCALE_PATTERNS}


def _build_form_data(args: dict[str, str]) -> dict[str, str]:
    """Build a dict of form values for template repopulation."""
    return dict(args)


def _render_error(error: str, form: dict[str, str]) -> tuple[str, int]:
    """Render the index page with an error alert."""
    scales = _get_scales()
    counts = _get_scale_interval_counts()
    return render_template(
        "index.html",
        scales=scales,
        form=form,
        error=error,
        scale_interval_counts_json=json.dumps(counts),
        notes=_CHROMATIC_NOTES,
        scale_colors=_SCALE_COLORS,
    ), 200


@pages_bp.get("/")
def index() -> str | Response:
    """Render the main page with form and optional diagram output."""
    scales = _get_scales()
    counts = _get_scale_interval_counts()

    # If no query params (or only empty ones), render empty form
    has_params = any(v != "" for v in request.args.values())
    if not has_params:
        return render_template(
            "index.html",
            scales=scales,
            form={},
            scale_interval_counts_json=json.dumps(counts),
            notes=_CHROMATIC_NOTES,
            scale_colors=_SCALE_COLORS,
        )

    # Filter out empty strings to avoid int("") crashes
    args = {k: v for k, v in request.args.items() if v != ""}
    form = _build_form_data(request.args)

    notes = current_app.config["NOTE_SERVICE"]
    catalog = current_app.config["SCALE_CATALOG"]
    engine = current_app.config["DIAGRAM_ENGINE"]

    is_partial = request.args.get("partial") == "1"

    try:
        params = parse_diagram_params(
            args, notes, catalog, allow_all_degrees=True
        )
    except HTTPException as exc:
        if is_partial:
            return Response(
                f'<div class="alert alert-danger">{html_mod.escape(str(exc.description))}</div>',
                mimetype="text/html",
            ), exc.code
        return _render_error(str(exc.description), form)

    title = f"{params.effective_root} {params.effective_scale.display_name}"

    if is_partial:
        return Response(
            _render_html5_fragment(params, title),
            mimetype="text/html",
        )

    return _render_html5(params, title, scales, form, counts)


def _render_html5_fragment(params: DiagramParams, title: str) -> str:
    """Return just the HTML5 diagram fragment (no template wrapper)."""
    html5_renderer = current_app.config["HTML5_RENDERER"]
    engine = current_app.config["DIAGRAM_ENGINE"]

    if params.all_degrees:
        data_list = engine.build_all_degrees(params)
        fragments = [
            html5_renderer.render(d.cells, d.fret_start, d.fret_end, d.title)
            for d in data_list
        ]
        return "\n".join(fragments)
    else:
        data = engine.build_single(params)
        return html5_renderer.render(data.cells, data.fret_start, data.fret_end, data.title)


def _render_html5(
    params: DiagramParams,
    title: str,
    scales: list[tuple[str, str]],
    form: dict[str, str],
    counts: dict[str, int],
) -> str:
    """Render the HTML5 preview template."""
    html_output = _render_html5_fragment(params, title)
    return render_template(
        "index.html",
        scales=scales,
        form=form,
        result=True,
        result_type="html5",
        html_output=html_output,
        diagram_title=title,
        scale_interval_counts_json=json.dumps(counts),
        notes=_CHROMATIC_NOTES,
        scale_colors=_SCALE_COLORS,
    )

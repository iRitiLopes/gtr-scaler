"""HTML frontend routes for the gtr-scaler web interface."""

from __future__ import annotations

import html as html_mod
import json

from flask import Blueprint, Response, current_app, render_template, request
from werkzeug.exceptions import HTTPException

from gtr_scaler.domain.scales import SCALE_PATTERNS
from gtr_scaler.server.validation import (
    DiagramParams,
    _parse_frets,
    compute_fret_start,
    parse_diagram_params,
)

pages_bp = Blueprint("pages", __name__)


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
            "index.html", scales=scales, form={}, scale_interval_counts_json=json.dumps(counts)
        )

    # Filter out empty strings to avoid int("") crashes
    args = {k: v for k, v in request.args.items() if v != ""}
    form = _build_form_data(request.args)

    notes = current_app.config["NOTE_SERVICE"]
    catalog = current_app.config["SCALE_CATALOG"]
    projector = current_app.config["PROJECTOR"]

    is_partial = request.args.get("partial") == "1"

    try:
        params = parse_diagram_params(
            args, notes, catalog, projector, allow_all_degrees=True
        )
        fret_start = compute_fret_start(projector, params)
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
            _render_html5_fragment(params, fret_start, title),
            mimetype="text/html",
        )

    return _render_html5(params, fret_start, title, scales, form, counts)


def _render_html5_fragment(params: DiagramParams, fret_start: int, title: str) -> str:
    """Return just the HTML5 diagram fragment (no template wrapper)."""
    html5_renderer = current_app.config["HTML5_RENDERER"]

    if params.all_degrees:
        projector = current_app.config["PROJECTOR"]
        fragments: list[str] = []
        for deg in range(1, len(params.effective_scale.intervals) + 1):
            fs = projector.degree_fret_start_with_shift(
                params.effective_root, params.effective_scale, deg, params.nps
            )
            _cells, fe = projector.project_n_notes(
                params.effective_root, params.effective_scale, params.nps, fs
            )
            deg_title = (
                f"{params.effective_root} {params.effective_scale.display_name}"
                f" \u2014 Shape {deg}"
            )
            fragment = html5_renderer.render(
                params.effective_root,
                params.effective_scale,
                fs,
                fe,
                notes_per_string=params.nps,
                title=deg_title,
            )
            fragments.append(fragment)
        return "\n".join(fragments)
    else:
        fret_start, fret_end = _resolve_fret_range(params, fret_start)
        return html5_renderer.render(
            params.effective_root,
            params.effective_scale,
            fret_start,
            fret_end,
            notes_per_string=params.nps,
            title=title,
        )


def _render_html5(
    params: DiagramParams,
    fret_start: int,
    title: str,
    scales: list[tuple[str, str]],
    form: dict[str, str],
    counts: dict[str, int],
) -> str:
    """Render the HTML5 preview template."""
    html_output = _render_html5_fragment(params, fret_start, title)
    return render_template(
        "index.html",
        scales=scales,
        form=form,
        result=True,
        result_type="html5",
        html_output=html_output,
        diagram_title=title,
        scale_interval_counts_json=json.dumps(counts),
    )


def _resolve_fret_range(params: DiagramParams, fret_start: int) -> tuple[int, int]:
    """Return (fret_start, fret_end) based on params.nps or params.frets."""
    projector = current_app.config["PROJECTOR"]

    if params.nps is not None:
        _cells, fret_end = projector.project_n_notes(
            params.effective_root, params.effective_scale, params.nps, fret_start
        )
        return fret_start, fret_end

    _base_start, fret_end = _parse_frets(params.frets)
    if params.start_degree != 1:
        fret_start = projector.degree_fret_start(
            params.effective_root, params.effective_scale, params.start_degree
        )
    return fret_start, fret_end

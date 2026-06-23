"""HTML frontend routes for the gtr-scaler web interface."""

from __future__ import annotations

import re

from flask import Blueprint, Response, current_app, render_template, request
from werkzeug.exceptions import HTTPException

from gtr_scaler.domain.scales import SCALE_PATTERNS
from gtr_scaler.renderers.multi import DiagramSpec
from gtr_scaler.server.validation import _parse_frets, compute_fret_start, parse_diagram_params

pages_bp = Blueprint("pages", __name__)


def _get_scales() -> list[tuple[str, str]]:
    """Return list of ``(key, display_name)`` for the scale dropdown."""
    catalog = current_app.config["SCALE_CATALOG"]
    return [(name, catalog.get(name).display_name) for name in SCALE_PATTERNS]


def _build_form_data(args: dict[str, str]) -> dict[str, str]:
    """Build a dict of form values for template repopulation."""
    return dict(args)


def _render_error(error: str, form: dict[str, str]) -> tuple[str, int]:
    """Render the index page with an error alert."""
    scales = _get_scales()
    return render_template("index.html", scales=scales, form=form, error=error), 200


@pages_bp.get("/")
def index() -> str | Response:
    """Render the main page with form and optional diagram output."""
    scales = _get_scales()

    # If no query params (or only empty ones), render empty form
    has_params = any(v != "" for v in request.args.values())
    if not has_params:
        return render_template("index.html", scales=scales, form={})

    # Filter out empty strings to avoid int("") crashes
    args = {k: v for k, v in request.args.items() if v != ""}
    form = _build_form_data(request.args)

    notes = current_app.config["NOTE_SERVICE"]
    catalog = current_app.config["SCALE_CATALOG"]
    projector = current_app.config["PROJECTOR"]

    try:
        params = parse_diagram_params(
            args, notes, catalog, projector, allow_all_degrees=True
        )
        fret_start = compute_fret_start(projector, params)
    except HTTPException as exc:
        return _render_error(str(exc.description), form)

    format_type = request.args.get("format", "ascii")
    title = f"{params.effective_root} {params.effective_scale.display_name}"

    # ── PDF download ──────────────────────────────────────────────────────────
    if format_type == "pdf":
        return _render_pdf(params, fret_start, title)

    # ── SVG inline preview ────────────────────────────────────────────────────
    if format_type == "svg":
        return _render_svg(params, fret_start, title, scales, form)

    # ── ASCII preview (default) ───────────────────────────────────────────────
    return _render_ascii(params, fret_start, title, scales, form)


def _render_pdf(params: object, fret_start: int, title: str) -> Response:
    """Generate and return a PDF download response."""
    svg_renderer = current_app.config["SVG_RENDERER"]
    pdf_converter = current_app.config["PDF_CONVERTER"]
    pdf_builder = current_app.config["PDF_BUILDER"]

    if params.all_degrees:
        specs, titles = _build_all_degree_specs(params, fret_start)
        pdf_bytes = pdf_builder.build(specs, titles=titles, max_per_page=3)
    else:
        fret_start, fret_end = _resolve_fret_range(params, fret_start)
        svg = svg_renderer.render(
            params.effective_root,
            params.effective_scale,
            fret_start,
            fret_end,
            notes_per_string=params.nps,
            title=title,
        )
        pdf_bytes = pdf_converter.svg_to_pdf(svg)

    filename = f"{params.effective_root}_{params.effective_scale.name}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _render_svg(
    params: object,
    fret_start: int,
    title: str,
    scales: list[tuple[str, str]],
    form: dict[str, str],
) -> str:
    """Render the SVG preview template."""
    svg_renderer = current_app.config["SVG_RENDERER"]
    multi_renderer = current_app.config["MULTI_RENDERER"]

    if params.all_degrees:
        specs, titles = _build_all_degree_specs(params, fret_start)
        svg = multi_renderer.render(specs, titles=titles)
        svg = re.sub(r"<\?xml[^?]*\?>\s*", "", svg)
        svg_outputs = [svg]
    else:
        fret_start, fret_end = _resolve_fret_range(params, fret_start)
        svg = svg_renderer.render(
            params.effective_root,
            params.effective_scale,
            fret_start,
            fret_end,
            notes_per_string=params.nps,
            title=title,
        )
        svg = re.sub(r"<\?xml[^?]*\?>\s*", "", svg)
        svg_outputs = [svg]

    return render_template(
        "index.html",
        scales=scales,
        form=form,
        result=True,
        result_type="svg",
        svg_outputs=svg_outputs,
        diagram_title=title,
    )


def _render_ascii(
    params: object,
    fret_start: int,
    title: str,
    scales: list[tuple[str, str]],
    form: dict[str, str],
) -> str:
    """Render the ASCII preview template."""
    ascii_renderer = current_app.config["ASCII_RENDERER"]

    fret_start, fret_end = _resolve_fret_range(params, fret_start)
    ascii_text = ascii_renderer.render(
        params.effective_root,
        params.effective_scale,
        fret_start,
        fret_end,
        notes_per_string=params.nps,
        title=title,
        color=False,
    )
    return render_template(
        "index.html",
        scales=scales,
        form=form,
        result=True,
        result_type="ascii",
        ascii_output=ascii_text,
        diagram_title=title,
    )


def _resolve_fret_range(params: object, fret_start: int) -> tuple[int, int]:
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


def _build_all_degree_specs(
    params: object, fret_start: int
) -> tuple[list[DiagramSpec], list[str]]:
    """Build diagram specs and titles for all-degrees rendering."""
    projector = current_app.config["PROJECTOR"]

    specs: list[DiagramSpec] = []
    titles: list[str] = []
    for deg in range(1, len(params.effective_scale.intervals) + 1):
        fs = projector.degree_fret_start_with_shift(
            params.effective_root, params.effective_scale, deg, params.nps
        )
        _cells, fe = projector.project_n_notes(
            params.effective_root, params.effective_scale, params.nps, fs
        )
        specs.append(
            DiagramSpec(
                root=params.effective_root,
                scale=params.effective_scale,
                fret_start=fs,
                fret_end=fe,
                notes_per_string=params.nps,
            )
        )
        titles.append(
            f"{params.effective_root} {params.effective_scale.display_name}"
            f" \u2014 Shape {deg}"
        )
    return specs, titles

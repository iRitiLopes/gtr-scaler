"""Flask route definitions for the gtr-scaler API."""

from __future__ import annotations

from flask import Flask, Response, current_app, jsonify, request

from gtr_scaler.renderers.multi import DiagramSpec
from gtr_scaler.server.serialization import serialize_diagram_data
from gtr_scaler.server.validation import _parse_frets, compute_fret_start, parse_diagram_params


def register_routes(app: Flask) -> None:  # noqa: C901
    """Register all HTTP routes on *app*."""

    # ── GET /scales ───────────────────────────────────────────────────────────
    @app.get("/scales")
    def list_scales():
        catalog = current_app.config["SCALE_CATALOG"]
        from gtr_scaler.domain.scales import SCALE_PATTERNS

        scales = [
            {"key": name, "display": catalog.get(name).display_name}
            for name in SCALE_PATTERNS
        ]
        return jsonify(scales)

    # ── GET /scales/<name> ────────────────────────────────────────────────────
    @app.get("/scales/<name>")
    def get_scale_data(name: str):
        notes = current_app.config["NOTE_SERVICE"]
        catalog = current_app.config["SCALE_CATALOG"]
        projector = current_app.config["PROJECTOR"]

        args = dict(request.args)
        args["scale"] = name
        params = parse_diagram_params(args, notes, catalog, projector)
        fret_start = compute_fret_start(projector, params)

        if params.nps is not None:
            cells, fret_end = projector.project_n_notes(
                params.effective_root, params.effective_scale, params.nps, fret_start
            )
        else:
            _base_start, fret_end = _parse_frets(params.frets)
            if params.start_degree != 1:
                fret_start = projector.degree_fret_start(
                    params.effective_root, params.effective_scale, params.start_degree
                )
            cells = projector.project(
                params.effective_root, params.effective_scale, fret_start, fret_end
            )

        data = serialize_diagram_data(
            root=params.effective_root,
            scale=params.effective_scale,
            mode=params.mode,
            start_degree=params.start_degree,
            fret_start=fret_start,
            fret_end=fret_end,
            nps=params.nps,
            cells=cells,
        )
        return jsonify(data)

    # ── GET /export/ascii ─────────────────────────────────────────────────────
    @app.get("/export/ascii")
    def export_ascii():
        notes = current_app.config["NOTE_SERVICE"]
        catalog = current_app.config["SCALE_CATALOG"]
        projector = current_app.config["PROJECTOR"]
        ascii_renderer = current_app.config["ASCII_RENDERER"]

        params = parse_diagram_params(
            dict(request.args), notes, catalog, projector, allow_all_degrees=False
        )
        fret_start = compute_fret_start(projector, params)

        if params.nps is not None:
            cells, fret_end = projector.project_n_notes(
                params.effective_root, params.effective_scale, params.nps, fret_start
            )
        else:
            _base_start, fret_end = _parse_frets(params.frets)
            if params.start_degree != 1:
                fret_start = projector.degree_fret_start(
                    params.effective_root, params.effective_scale, params.start_degree
                )

        text = ascii_renderer.render(
            params.effective_root,
            params.effective_scale,
            fret_start,
            fret_end,
            notes_per_string=params.nps,
            color=False,
        )
        return Response(text, mimetype="text/plain; charset=utf-8")

    # ── GET /export/svg ───────────────────────────────────────────────────────
    @app.get("/export/svg")
    def export_svg():
        notes = current_app.config["NOTE_SERVICE"]
        catalog = current_app.config["SCALE_CATALOG"]
        projector = current_app.config["PROJECTOR"]
        svg_renderer = current_app.config["SVG_RENDERER"]
        multi_renderer = current_app.config["MULTI_RENDERER"]

        params = parse_diagram_params(
            dict(request.args), notes, catalog, projector, allow_all_degrees=True
        )

        if params.all_degrees:
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
            svg = multi_renderer.render(specs, titles=titles)
        else:
            fret_start = compute_fret_start(projector, params)
            if params.nps is not None:
                _cells, fret_end = projector.project_n_notes(
                    params.effective_root, params.effective_scale, params.nps, fret_start
                )
            else:
                _base_start, fret_end = _parse_frets(params.frets)
                if params.start_degree != 1:
                    fret_start = projector.degree_fret_start(
                        params.effective_root, params.effective_scale, params.start_degree
                    )
            title = f"{params.effective_root} {params.effective_scale.display_name}"
            svg = svg_renderer.render(
                params.effective_root,
                params.effective_scale,
                fret_start,
                fret_end,
                notes_per_string=params.nps,
                title=title,
            )

        return Response(svg, mimetype="image/svg+xml")

    # ── GET /export/pdf ───────────────────────────────────────────────────────
    @app.get("/export/pdf")
    def export_pdf():
        notes = current_app.config["NOTE_SERVICE"]
        catalog = current_app.config["SCALE_CATALOG"]
        projector = current_app.config["PROJECTOR"]
        svg_renderer = current_app.config["SVG_RENDERER"]
        pdf_converter = current_app.config["PDF_CONVERTER"]
        pdf_builder = current_app.config["PDF_BUILDER"]

        params = parse_diagram_params(
            dict(request.args), notes, catalog, projector, allow_all_degrees=True
        )

        if params.all_degrees:
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
            pdf_bytes = pdf_builder.build(specs, titles=titles, max_per_page=3)
        else:
            fret_start = compute_fret_start(projector, params)
            if params.nps is not None:
                _cells, fret_end = projector.project_n_notes(
                    params.effective_root, params.effective_scale, params.nps, fret_start
                )
            else:
                _base_start, fret_end = _parse_frets(params.frets)
                if params.start_degree != 1:
                    fret_start = projector.degree_fret_start(
                        params.effective_root, params.effective_scale, params.start_degree
                    )
            title = f"{params.effective_root} {params.effective_scale.display_name}"
            svg = svg_renderer.render(
                params.effective_root,
                params.effective_scale,
                fret_start,
                fret_end,
                notes_per_string=params.nps,
                title=title,
            )
            pdf_bytes = pdf_converter.svg_to_pdf(svg)

        return Response(pdf_bytes, mimetype="application/pdf")


"""Flask route definitions for the gtr-scaler API."""

from __future__ import annotations

from flask import Flask, Response, current_app, jsonify, request

from gtr_scaler.server.serialization import serialize_diagram_data
from gtr_scaler.server.validation import parse_diagram_params


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
        builder = current_app.config["DIAGRAM_BUILDER"]

        args = dict(request.args)
        args["scale"] = name
        params = parse_diagram_params(args, notes, catalog)

        cells, fret_start, fret_end = builder.build(params)

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
        engine = current_app.config["DIAGRAM_ENGINE"]
        ascii_renderer = current_app.config["ASCII_RENDERER"]

        params = parse_diagram_params(
            dict(request.args), notes, catalog, allow_all_degrees=False
        )
        data = engine.build_single(params)
        text = ascii_renderer.render(data.cells, data.fret_start, data.fret_end, data.title, color=False)
        return Response(text, mimetype="text/plain; charset=utf-8")

    # ── GET /export/svg ───────────────────────────────────────────────────────
    @app.get("/export/svg")
    def export_svg():
        notes = current_app.config["NOTE_SERVICE"]
        catalog = current_app.config["SCALE_CATALOG"]
        engine = current_app.config["DIAGRAM_ENGINE"]
        svg_renderer = current_app.config["SVG_RENDERER"]
        svg_post_processor = current_app.config["SVG_POST_PROCESSOR"]
        multi_renderer = current_app.config["MULTI_RENDERER"]

        params = parse_diagram_params(
            dict(request.args), notes, catalog, allow_all_degrees=True
        )

        if params.all_degrees:
            data_list = engine.build_all_degrees(params)
            svg = multi_renderer.render(data_list)
        else:
            data = engine.build_single(params)
            raw = svg_renderer.render(data.cells, data.fret_start, data.fret_end)
            svg = svg_post_processor.process(raw, data.title)

        return Response(svg, mimetype="image/svg+xml")

    # ── GET /export/pdf ───────────────────────────────────────────────────────
    @app.get("/export/pdf")
    def export_pdf():
        notes = current_app.config["NOTE_SERVICE"]
        catalog = current_app.config["SCALE_CATALOG"]
        engine = current_app.config["DIAGRAM_ENGINE"]
        svg_renderer = current_app.config["SVG_RENDERER"]
        svg_post_processor = current_app.config["SVG_POST_PROCESSOR"]
        pdf_converter = current_app.config["PDF_CONVERTER"]
        pdf_builder = current_app.config["PDF_BUILDER"]

        params = parse_diagram_params(
            dict(request.args), notes, catalog, allow_all_degrees=True
        )

        if params.all_degrees:
            data_list = engine.build_all_degrees(params)
            pdf_bytes = pdf_builder.build(data_list)
        else:
            data = engine.build_single(params)
            raw = svg_renderer.render(data.cells, data.fret_start, data.fret_end)
            svg = svg_post_processor.process(raw, data.title)
            pdf_bytes = pdf_converter.svg_to_pdf(svg)

        return Response(pdf_bytes, mimetype="application/pdf")

"""Flask application factory for gtr-scaler."""

from __future__ import annotations

from flask import Flask

from gtr_scaler.builder import DiagramBuilder
from gtr_scaler.domain.fretboard import FretboardProjector
from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import ScaleCatalog
from gtr_scaler.engine import DiagramEngine
from gtr_scaler.exporters.pdf import MultiPagePdfBuilder, PdfConverter
from gtr_scaler.renderers.ascii import AsciiRenderer
from gtr_scaler.renderers.html5 import Html5Renderer
from gtr_scaler.renderers.multi import MultiDiagramRenderer
from gtr_scaler.renderers.svg import SvgPostProcessor, SvgRenderer
from gtr_scaler.server.error_handlers import register_error_handlers
from gtr_scaler.server.routes import register_routes


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # ── Instantiate domain services (same wiring as __main__._build_app) ──────
    notes = NoteService()
    catalog = ScaleCatalog(notes)
    projector = FretboardProjector(notes)
    builder = DiagramBuilder(projector)
    engine = DiagramEngine(builder)
    ascii_renderer = AsciiRenderer(color=False)
    svg_renderer = SvgRenderer()
    svg_post_processor = SvgPostProcessor()
    multi_renderer = MultiDiagramRenderer(svg_renderer, svg_post_processor)
    html5_renderer = Html5Renderer()
    pdf_converter = PdfConverter()
    pdf_builder = MultiPagePdfBuilder(svg_renderer, multi_renderer, pdf_converter)

    # Store dependencies in app.config for route handlers to access via
    # ``flask.current_app.config``.
    app.config["NOTE_SERVICE"] = notes
    app.config["SCALE_CATALOG"] = catalog
    app.config["PROJECTOR"] = projector
    app.config["DIAGRAM_BUILDER"] = builder
    app.config["DIAGRAM_ENGINE"] = engine
    app.config["ASCII_RENDERER"] = ascii_renderer
    app.config["SVG_RENDERER"] = svg_renderer
    app.config["SVG_POST_PROCESSOR"] = svg_post_processor
    app.config["MULTI_RENDERER"] = multi_renderer
    app.config["HTML5_RENDERER"] = html5_renderer
    app.config["PDF_CONVERTER"] = pdf_converter
    app.config["PDF_BUILDER"] = pdf_builder

    register_error_handlers(app)
    register_routes(app)

    from gtr_scaler.server.routes_html import pages_bp

    app.register_blueprint(pages_bp)

    return app

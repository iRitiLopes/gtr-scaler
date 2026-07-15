"""Entry point: python -m gtr_scaler"""

import argparse
import sys

from gtr_scaler.app import GtrScalerApp
from gtr_scaler.builder import DiagramBuilder
from gtr_scaler.domain.fretboard import FretboardProjector
from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import SCALE_PATTERNS, ScaleCatalog
from gtr_scaler.engine import DiagramEngine
from gtr_scaler.exporters.file_writer import FileWriter
from gtr_scaler.exporters.pdf import MultiPagePdfBuilder, PdfConverter
from gtr_scaler.renderers.ascii import AsciiRenderer
from gtr_scaler.renderers.multi import MultiDiagramRenderer
from gtr_scaler.renderers.svg import SvgPostProcessor, SvgRenderer


def _parse_render_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gtr-scaler",
        description="Guitar scale fretboard viewer",
    )
    parser.add_argument("root", nargs="?", default="A", help="Root note (default: A)")
    parser.add_argument(
        "scale",
        nargs="?",
        default="pentatonic_minor",
        help=f"Scale name (default: pentatonic_minor). Available: {', '.join(SCALE_PATTERNS)}",
    )

    fret_group = parser.add_mutually_exclusive_group()
    fret_group.add_argument(
        "--frets",
        default="12",
        metavar="N or START-END",
        help="Fret range: single number (0 to N) or START-END (default: 12)",
    )
    fret_group.add_argument(
        "--notes",
        type=int,
        default=None,
        metavar="N",
        help="Notes per string flowing continuously across strings; "
        "fretboard ends at the last note needed (mutually exclusive with --frets)",
    )

    parser.add_argument(
        "--mode", type=int, default=1, metavar="N", help="Mode degree, 1-indexed (default: 1)"
    )
    parser.add_argument(
        "--start-degree",
        type=int,
        default=1,
        metavar="N",
        help="Scale degree to start from on the low E string, 1-indexed (default: 1 = root)",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Export to file instead of printing ASCII. Extension determines format: .svg or .pdf",
    )
    parser.add_argument(
        "--all-degrees",
        action="store_true",
        default=False,
        help="Generate one diagram per scale degree (requires --notes with value 2-4)",
    )

    return parser.parse_args()


def _parse_serve_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gtr-scaler serve",
        description="Run the gtr-scaler Flask web server",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0 — accessible on local network)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable Flask debug mode",
    )
    return parser.parse_args()


def _build_app() -> GtrScalerApp:
    notes = NoteService()
    catalog = ScaleCatalog(notes)
    projector = FretboardProjector(notes)
    builder = DiagramBuilder(projector)
    engine = DiagramEngine(builder)
    ascii_renderer = AsciiRenderer(color=None)
    svg_renderer = SvgRenderer()
    svg_post_processor = SvgPostProcessor()
    multi_renderer = MultiDiagramRenderer(svg_renderer, svg_post_processor)
    pdf_converter = PdfConverter()
    pdf_builder = MultiPagePdfBuilder(svg_renderer, multi_renderer, pdf_converter)
    file_writer = FileWriter()
    return GtrScalerApp(
        catalog,
        engine,
        ascii_renderer,
        svg_renderer,
        svg_post_processor,
        multi_renderer,
        pdf_converter,
        pdf_builder,
        file_writer,
    )


def _cli_main() -> int:
    args = _parse_render_args()
    app = _build_app()
    return app.run(args)


def _serve_main() -> int:
    args = _parse_serve_args()
    from gtr_scaler.server.app import create_app

    app = create_app()
    print(f"Starting gtr-scaler server on http://{args.host}:{args.port}")
    if args.host == "0.0.0.0":
        print("Server is accessible from other devices on your local network.")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # Remove "serve" from argv so the server parser doesn't see it
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        return _serve_main()
    return _cli_main()


if __name__ == "__main__":
    raise SystemExit(main())

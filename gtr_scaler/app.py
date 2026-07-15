"""Application orchestrator — wires domain + renderers + exporters together."""

import argparse
import sys
from pathlib import Path

from gtr_scaler.diagram_params import DiagramData, DiagramParams
from gtr_scaler.domain.scales import ScaleCatalog
from gtr_scaler.engine import DiagramEngine
from gtr_scaler.exporters.file_writer import FileWriter
from gtr_scaler.exporters.pdf import MultiPagePdfBuilder, PdfConverter
from gtr_scaler.renderers.ascii import AsciiRenderer
from gtr_scaler.renderers.multi import MultiDiagramRenderer
from gtr_scaler.renderers.svg import SvgPostProcessor, SvgRenderer


class GtrScalerApp:
    """Top-level application facade."""

    def __init__(
        self,
        scale_catalog: ScaleCatalog,
        engine: DiagramEngine,
        ascii_renderer: AsciiRenderer,
        svg_renderer: SvgRenderer,
        svg_post_processor: SvgPostProcessor,
        multi_renderer: MultiDiagramRenderer,
        pdf_converter: PdfConverter,
        pdf_builder: MultiPagePdfBuilder,
        file_writer: FileWriter,
    ) -> None:
        self._scale_catalog = scale_catalog
        self._engine = engine
        self._ascii_renderer = ascii_renderer
        self._svg_renderer = svg_renderer
        self._svg_post_processor = svg_post_processor
        self._multi_renderer = multi_renderer
        self._pdf_converter = pdf_converter
        self._pdf_builder = pdf_builder
        self._file_writer = file_writer

    def run(self, args: argparse.Namespace) -> int:
        """Execute the CLI command. Returns 0 on success, 1 on error."""
        try:
            scale = self._scale_catalog.get(args.scale)
            root = args.root
            if args.mode != 1:
                root = self._scale_catalog.degree_root(root, scale, args.mode)
                scale = self._scale_catalog.compute_mode(scale, args.mode)

            params = DiagramParams(
                root=args.root,
                scale_name=args.scale,
                scale=scale,
                mode=args.mode,
                start_degree=args.start_degree,
                frets=args.frets,
                nps=args.notes,
                all_degrees=args.all_degrees,
                effective_root=root,
                effective_scale=scale,
            )

            if params.all_degrees:
                data_list = self._engine.build_all_degrees(params)
                if args.output is None:
                    diagrams = [
                        self._ascii_renderer.render(
                            d.cells, d.fret_start, d.fret_end, d.title
                        )
                        for d in data_list
                    ]
                    print("\n\n".join(diagrams))
                else:
                    ext = Path(args.output).suffix.lower()
                    if ext == ".svg":
                        svg = self._multi_renderer.render(data_list)
                        self._file_writer.write_text(args.output, svg)
                    elif ext == ".pdf":
                        pdf_bytes = self._pdf_builder.build(data_list)
                        self._file_writer.write_bytes(args.output, pdf_bytes)
                    else:
                        print(
                            f"Error: unsupported output format {ext!r} (use .svg or .pdf)",
                            file=sys.stderr,
                        )
                        return 1
                    print(f"Saved: {args.output}")
            else:
                data = self._engine.build_single(params)
                if args.output is None:
                    print(
                        self._ascii_renderer.render(
                            data.cells, data.fret_start, data.fret_end, data.title
                        )
                    )
                else:
                    ext = Path(args.output).suffix.lower()
                    if ext == ".svg":
                        raw = self._svg_renderer.render(
                            data.cells, data.fret_start, data.fret_end
                        )
                        svg = self._svg_post_processor.process(raw, data.title)
                        self._file_writer.write_text(args.output, svg)
                    elif ext == ".pdf":
                        raw = self._svg_renderer.render(
                            data.cells, data.fret_start, data.fret_end
                        )
                        svg = self._svg_post_processor.process(raw, data.title)
                        pdf_bytes = self._pdf_converter.svg_to_pdf(svg)
                        self._file_writer.write_bytes(args.output, pdf_bytes)
                    else:
                        print(
                            f"Error: unsupported output format {ext!r} (use .svg or .pdf)",
                            file=sys.stderr,
                        )
                        return 1
                    print(f"Saved: {args.output}")

        except (ValueError, argparse.ArgumentTypeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        return 0

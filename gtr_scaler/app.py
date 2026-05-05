"""Application orchestrator — wires domain + renderers + exporters together."""

import argparse
import sys
from pathlib import Path

from gtr_scaler.domain.fretboard import FretboardProjector
from gtr_scaler.domain.scales import Scale, ScaleCatalog
from gtr_scaler.exporters.file_writer import FileWriter
from gtr_scaler.exporters.pdf import MultiPagePdfBuilder, PdfConverter
from gtr_scaler.renderers.ascii import AsciiRenderer
from gtr_scaler.renderers.multi import DiagramSpec, MultiDiagramRenderer
from gtr_scaler.renderers.svg import SvgRenderer


class GtrScalerApp:
    """Top-level application facade."""

    def __init__(
        self,
        scale_catalog: ScaleCatalog,
        projector: FretboardProjector,
        ascii_renderer: AsciiRenderer,
        svg_renderer: SvgRenderer,
        multi_renderer: MultiDiagramRenderer,
        pdf_converter: PdfConverter,
        pdf_builder: MultiPagePdfBuilder,
        file_writer: FileWriter,
    ) -> None:
        self._scale_catalog = scale_catalog
        self._projector = projector
        self._ascii_renderer = ascii_renderer
        self._svg_renderer = svg_renderer
        self._multi_renderer = multi_renderer
        self._pdf_converter = pdf_converter
        self._pdf_builder = pdf_builder
        self._file_writer = file_writer

    @staticmethod
    def _parse_frets(value: str) -> tuple[int, int]:
        """Accept '22' → (0, 22) or '5-9' → (5, 9)."""
        if "-" in value:
            parts = value.split("-", 1)
            start, end = int(parts[0]), int(parts[1])
            if start < 0 or end < start:
                raise argparse.ArgumentTypeError(
                    f"Invalid fret range {value!r}: need start >= 0 and end >= start"
                )
            return start, end
        n = int(value)
        if n < 0:
            raise argparse.ArgumentTypeError(f"Frets must be >= 0, got {n}")
        return 0, n

    def _get_render_params(
        self,
        root: str,
        scale: Scale,
        notes: int | None,
        frets: str,
        start_degree: int,
    ) -> tuple[int, int, int | None]:
        """Compute fret_start, fret_end, and notes_per_string for a given degree."""
        if notes is not None:
            fret_start = self._projector.degree_fret_start_with_shift(
                root, scale, start_degree, notes
            )
            notes_per_string = notes
            # fret_end is ignored when notes_per_string is set;
            # projector.project_n_notes computes the real end
            fret_end = 12
        else:
            notes_per_string = None
            base_start, fret_end = self._parse_frets(frets)
            fret_start = (
                self._projector.degree_fret_start(root, scale, start_degree)
                if start_degree != 1
                else base_start
            )
        return fret_start, fret_end, notes_per_string

    def run(self, args: argparse.Namespace) -> int:
        """Execute the CLI command. Returns 0 on success, 1 on error."""
        try:
            if args.all_degrees and (args.notes is None or not 2 <= args.notes <= 4):
                raise ValueError(
                    "--all-degrees requires --notes with a value between 2 and 4"
                )

            if args.all_degrees and args.start_degree != 1:
                raise ValueError("--all-degrees cannot be used with --start-degree")

            scale = self._scale_catalog.get(args.scale)
            root = args.root
            if args.mode != 1:
                root = self._scale_catalog.degree_root(root, scale, args.mode)
                scale = self._scale_catalog.compute_mode(scale, args.mode)

            if args.all_degrees:
                diagrams: list[str] = []
                diagram_specs: list[DiagramSpec] = []
                titles: list[str] = []
                for deg in range(1, len(scale.intervals) + 1):
                    fs, fe, nps = self._get_render_params(
                        root, scale, args.notes, args.frets, deg
                    )
                    shape_label = f"Shape {deg}"
                    if args.output is None:
                        diagrams.append(
                            self._ascii_renderer.render(
                                root,
                                scale,
                                fs,
                                fe,
                                notes_per_string=nps,
                                title=f"{root} {scale.display_name} \u2014 {shape_label}",
                            )
                        )
                    else:
                        diagram_specs.append(
                            DiagramSpec(
                                root=root,
                                scale=scale,
                                fret_start=fs,
                                fret_end=fe,
                                notes_per_string=nps,
                            )
                        )
                        titles.append(
                            f"{root} {scale.display_name} \u2014 {shape_label}"
                        )
                if args.output is None:
                    print("\n\n".join(diagrams))
                else:
                    ext = Path(args.output).suffix.lower()
                    if ext == ".svg":
                        svg = self._multi_renderer.render(diagram_specs, titles=titles)
                        self._file_writer.write_text(args.output, svg)
                    elif ext == ".pdf":
                        pdf_bytes = self._pdf_builder.build(
                            diagram_specs, titles=titles, max_per_page=3
                        )
                        self._file_writer.write_bytes(args.output, pdf_bytes)
                    else:
                        print(
                            f"Error: unsupported output format {ext!r} (use .svg or .pdf)",
                            file=sys.stderr,
                        )
                        return 1
                    print(f"Saved: {args.output}")
            else:
                fs, fe, nps = self._get_render_params(
                    root, scale, args.notes, args.frets, args.start_degree
                )
                if args.output is None:
                    print(
                        self._ascii_renderer.render(
                            root, scale, fs, fe, notes_per_string=nps
                        )
                    )
                else:
                    title = f"{root} {scale.display_name}"
                    ext = Path(args.output).suffix.lower()
                    if ext == ".svg":
                        svg = self._svg_renderer.render(
                            root,
                            scale,
                            fs,
                            fe,
                            notes_per_string=nps,
                            title=title,
                        )
                        self._file_writer.write_text(args.output, svg)
                    elif ext == ".pdf":
                        svg = self._svg_renderer.render(
                            root,
                            scale,
                            fs,
                            fe,
                            notes_per_string=nps,
                            title=title,
                        )
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

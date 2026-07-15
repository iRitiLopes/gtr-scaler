"""PDF export utilities — converter and multi-page builder."""

from io import BytesIO
from pathlib import Path

from gtr_scaler.diagram_params import DiagramData
from gtr_scaler.renderers.multi import MultiDiagramRenderer
from gtr_scaler.renderers.svg import SvgRenderer


class PdfConverter:
    """Converts SVG strings to PDF bytes via cairosvg."""

    def svg_to_pdf(self, svg: str) -> bytes:
        """Convert an SVG string to PDF bytes."""
        try:
            import cairosvg
        except ImportError as exc:
            raise RuntimeError(
                "cairosvg is required for PDF export: pip install cairosvg"
            ) from exc

        result = cairosvg.svg2pdf(bytestring=svg.encode())
        if result is not None:
            return result

        # Older cairosvg may require write_to; use temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=tmp_path)
        page_bytes = Path(tmp_path).read_bytes()
        Path(tmp_path).unlink()
        return page_bytes


class MultiPagePdfBuilder:
    """Builds multi-page PDF documents from diagram specs."""

    def __init__(
        self,
        svg_renderer: SvgRenderer,
        multi_renderer: MultiDiagramRenderer,
        converter: PdfConverter,
    ) -> None:
        self._svg_renderer = svg_renderer
        self._multi_renderer = multi_renderer
        self._converter = converter

    def build(
        self,
        diagrams: list[DiagramData],
        max_per_page: int = 3,
    ) -> bytes:
        """Build a multi-page PDF from diagram data.

        Diagrams are split into chunks of ``max_per_page`` per page.
        Each chunk is rendered as a single SVG, converted to PDF,
        then all pages are merged with pypdf.
        """
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError as exc:
            raise RuntimeError(
                "pypdf is required for multi-page PDF export: pip install pypdf"
            ) from exc

        # Split into chunks
        page_bytes_list: list[bytes] = []
        for start in range(0, len(diagrams), max_per_page):
            end = start + max_per_page
            chunk = diagrams[start:end]
            page_svg = self._multi_renderer.render(chunk)
            page_bytes = self._converter.svg_to_pdf(page_svg)
            page_bytes_list.append(page_bytes)

        # Merge pages
        writer = PdfWriter()
        for page_data in page_bytes_list:
            reader = PdfReader(BytesIO(page_data))
            for page in reader.pages:
                writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()

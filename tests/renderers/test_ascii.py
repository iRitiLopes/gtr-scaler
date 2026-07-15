from gtr_scaler.domain.fretboard import FretboardProjector
from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import ScaleCatalog
from gtr_scaler.renderers.ascii import AsciiRenderer

notes = NoteService()
catalog = ScaleCatalog(notes)
projector = FretboardProjector(notes)
renderer = AsciiRenderer(color=False)


def test_render_a_minor_pentatonic_3nps_fret_start_5():
    scale = catalog.get("pentatonic_minor")
    cells, fret_end = projector.project_n_notes("A", scale, 3, 5)
    result = renderer.render(cells, fret_start=5, fret_end=fret_end, title="A Pentatonic Minor")
    expected = "\n".join(
        [
            "A Pentatonic Minor  |  Standard tuning (E A D G B e)",
            "",
            "       5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20   21   22",
            "e  |----|----|----|----|----|----|----|----|----|----|----|----|-R--|----|----|-b3-|----|-4--|",
            "B  |----|----|----|----|----|----|----|----|----|----|-4--|----|-5--|----|----|-b7-|----|----|",
            "G  |----|----|----|----|----|----|----|-b7-|----|-R--|----|----|-b3-|----|----|----|----|----|",
            "D  |----|----|----|----|----|-b3-|----|-4--|----|-5--|----|----|----|----|----|----|----|----|",
            "A  |----|----|-5--|----|----|-b7-|----|-R--|----|----|----|----|----|----|----|----|----|----|",
            "E  |-R--|----|----|-b3-|----|-4--|----|----|----|----|----|----|----|----|----|----|----|----|",
            "",
            "  R=1   b3=m3   4=P4   5=P5   b7=m7",
        ]
    )
    assert result == expected


def test_render_with_shape_label():
    scale = catalog.get("pentatonic_minor")
    cells = projector.project("A", scale, 0, 12)
    result = renderer.render(cells, fret_start=0, fret_end=12, title="A Pentatonic Minor \u2014 Shape 1")
    header = result.split("\n")[0]
    assert "Shape 1" in header
    assert "\u2014" in header
    assert "A Pentatonic Minor" in header


def test_render_without_shape_label():
    scale = catalog.get("pentatonic_minor")
    cells = projector.project("A", scale, 0, 12)
    result = renderer.render(cells, fret_start=0, fret_end=12, title="A Pentatonic Minor")
    header = result.split("\n")[0]
    assert "\u2014" not in header
    assert header == "A Pentatonic Minor  |  Standard tuning (E A D G B e)"

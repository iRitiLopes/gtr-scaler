from gtr_scaler.domain.scales import get_scale
from gtr_scaler.renderers.ascii import render


def test_render_a_minor_pentatonic_3nps_fret_start_5():
    scale = get_scale("pentatonic_minor")
    result = render("A", scale, fret_start=5, notes_per_string=3, color=False)
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

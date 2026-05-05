import pytest

from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import ScaleCatalog

notes = NoteService()
catalog = ScaleCatalog(notes)


def test_mode1_is_identity():
    scale = catalog.get("pentatonic_major")
    assert catalog.compute_mode(scale, 1) is scale


def test_pentatonic_major_mode5_is_minor_pentatonic():
    # Classic relationship: mode 5 of major pentatonic = minor pentatonic
    major_pent = catalog.get("pentatonic_major")
    minor_pent = catalog.get("pentatonic_minor")
    mode5 = catalog.compute_mode(major_pent, 5)
    assert mode5.semitones == minor_pent.semitones


def test_major_mode2_is_dorian():
    major = catalog.get("major")
    dorian = catalog.get("dorian")
    assert catalog.compute_mode(major, 2).semitones == dorian.semitones


def test_major_mode6_is_aeolian():
    major = catalog.get("major")
    aeolian = catalog.get("aeolian")
    assert catalog.compute_mode(major, 6).semitones == aeolian.semitones


def test_all_major_modes_start_with_zero():
    major = catalog.get("major")
    for degree in range(1, 8):
        mode = catalog.compute_mode(major, degree)
        assert mode.semitones[0] == 0, f"Mode {degree} does not start at 0"


def test_mode_degree_out_of_range():
    scale = catalog.get("pentatonic_minor")  # 5-note scale
    with pytest.raises(ValueError, match="out of range"):
        catalog.compute_mode(scale, 6)


def test_major_mode_display_names():
    major = catalog.get("major")
    assert catalog.compute_mode(major, 2).display_name == "Dorian"
    assert catalog.compute_mode(major, 3).display_name == "Phrygian"
    assert catalog.compute_mode(major, 5).display_name == "Mixolydian"


def test_pentatonic_mode_display_names():
    pent = catalog.get("pentatonic_major")
    assert catalog.compute_mode(pent, 5).display_name == "Minor Pentatonic"
    assert catalog.compute_mode(pent, 2).display_name == "Egyptian"


class TestDegreeRoot:
    def test_degree1_returns_root(self):
        assert catalog.degree_root("C", catalog.get("major"), 1) == "C"

    def test_c_major_degree6_is_a(self):
        # C D E F G A B — 6th degree is A
        assert catalog.degree_root("C", catalog.get("major"), 6) == "A"

    def test_c_major_degree2_is_d(self):
        assert catalog.degree_root("C", catalog.get("major"), 2) == "D"

    def test_c_pentatonic_major_degree5_is_a(self):
        # C major pentatonic: C D E G A — 5th degree is A
        assert catalog.degree_root("C", catalog.get("pentatonic_major"), 5) == "A"

    def test_a_major_degree6_is_f_sharp(self):
        # A B C# D E F# G# — 6th degree is F#
        assert catalog.degree_root("A", catalog.get("major"), 6) == "F#"

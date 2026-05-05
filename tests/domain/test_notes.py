import pytest

from gtr_scaler.domain.notes import NoteService

notes = NoteService()


def test_natural_notes():
    assert notes.to_semitone("C") == 0
    assert notes.to_semitone("A") == 9
    assert notes.to_semitone("E") == 4


def test_sharps():
    assert notes.to_semitone("C#") == 1
    assert notes.to_semitone("F#") == 6


def test_flats_resolve_to_sharps():
    assert notes.to_semitone("Bb") == notes.to_semitone("A#")
    assert notes.to_semitone("Eb") == notes.to_semitone("D#")
    assert notes.to_semitone("Gb") == notes.to_semitone("F#")


def test_unknown_note_raises():
    with pytest.raises(ValueError, match="Unknown note"):
        notes.to_semitone("X")


def test_semitone_to_note_roundtrip():
    for i in range(12):
        note = notes.to_name(i)
        assert notes.to_semitone(note) == i

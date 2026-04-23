import pytest
from gtr_scaler.domain.notes import note_to_semitone, semitone_to_note


def test_natural_notes():
    assert note_to_semitone('C') == 0
    assert note_to_semitone('A') == 9
    assert note_to_semitone('E') == 4


def test_sharps():
    assert note_to_semitone('C#') == 1
    assert note_to_semitone('F#') == 6


def test_flats_resolve_to_sharps():
    assert note_to_semitone('Bb') == note_to_semitone('A#')
    assert note_to_semitone('Eb') == note_to_semitone('D#')
    assert note_to_semitone('Gb') == note_to_semitone('F#')


def test_unknown_note_raises():
    with pytest.raises(ValueError, match="Unknown note"):
        note_to_semitone('X')


def test_semitone_to_note_roundtrip():
    for i in range(12):
        note = semitone_to_note(i)
        assert note_to_semitone(note) == i

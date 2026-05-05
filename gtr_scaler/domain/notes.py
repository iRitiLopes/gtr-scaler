"""Chromatic note utilities — no I/O, no side effects."""

CHROMATIC: tuple[str, ...] = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Flat → sharp enharmonic equivalents
_ENHARMONICS: dict[str, str] = {
    "Cb": "B",
    "Db": "C#",
    "Eb": "D#",
    "Fb": "E",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
}


class NoteService:
    """Encapsulates chromatic note lookup logic."""

    def to_semitone(self, note: str) -> int:
        """Return 0-11 semitone index for a note name (sharps or flats accepted)."""
        canonical = _ENHARMONICS.get(note, note)
        try:
            return CHROMATIC.index(canonical)
        except ValueError:
            raise ValueError(f"Unknown note: {note!r}") from None

    def to_name(self, semitone: int) -> str:
        """Return the sharp-spelling note name for a 0-11 semitone index."""
        return CHROMATIC[semitone % 12]

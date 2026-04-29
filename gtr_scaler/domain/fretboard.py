"""Fretboard model and scale projection."""

from dataclasses import dataclass

from .notes import note_to_semitone
from .scales import Scale

# Standard tuning: low E → high E
STRING_NAMES: tuple[str, ...] = ("E", "A", "D", "G", "B", "e")
_OPEN_SEMITONES: tuple[int, ...] = tuple(
    note_to_semitone(n) for n in ("E", "A", "D", "G", "B", "E")
)


@dataclass(frozen=True)
class FretCell:
    string_idx: int  # 0 = low E, 5 = high e
    fret: int
    interval: str  # interval symbol, e.g. '1', 'm3', 'P5'

    @property
    def is_root(self) -> bool:
        return self.interval == "1"


def project_scale(
    root: str, scale: Scale, fret_start: int = 0, fret_end: int = 12
) -> list[FretCell]:
    """Return all fretboard positions that belong to the scale within [fret_start, fret_end]."""
    root_semitone = note_to_semitone(root)
    pitch_to_interval: dict[int, str] = {
        (root_semitone + semitone) % 12: symbol
        for symbol, semitone in zip(scale.intervals, scale.semitones)
    }

    cells: list[FretCell] = []
    for string_idx, open_semitone in enumerate(_OPEN_SEMITONES):
        for fret in range(fret_start, fret_end + 1):
            pitch = (open_semitone + fret) % 12
            if pitch in pitch_to_interval:
                cells.append(
                    FretCell(
                        string_idx=string_idx,
                        fret=fret,
                        interval=pitch_to_interval[pitch],
                    )
                )
    return cells


def _first_note_gte(open_semitone: int, target_pitch: int, min_fret: int) -> int:
    """First fret >= min_fret on a string where the given pitch class occurs."""
    base = (target_pitch - open_semitone + 12) % 12
    if base < min_fret:
        offset = min_fret - base
        base += 12 * ((offset + 11) // 12)
    return base


def project_scale_n_notes(
    root: str, scale: Scale, notes_per_string: int, fret_start: int = 0
) -> tuple[list[FretCell], int]:
    """Return cells for exactly notes_per_string scale notes per string.

    The scale flows continuously across strings: each string picks up the next
    note in the scale sequence after where the previous string ended.
    Each new string starts at the first occurrence of its opening note that is
    >= the previous string's starting fret (keeps the pattern ascending).

    Returns (cells, fret_end) where fret_end is the highest fret used.
    """
    root_semitone = note_to_semitone(root)
    scale_pitches = tuple((root_semitone + s) % 12 for s in scale.semitones)
    pitch_to_interval: dict[int, str] = dict(zip(scale_pitches, scale.intervals))

    _MAX_EXTRA = 48  # safety cap per string

    cells: list[FretCell] = []
    max_fret = fret_start

    # Which scale-degree index to look for at the start of each string
    next_pitch_idx: int = 0
    # Minimum fret for the next string's opening note (keeps pattern ascending)
    min_fret_for_next: int = fret_start

    for string_num, (string_idx, open_semitone) in enumerate(
        zip(range(len(_OPEN_SEMITONES)), _OPEN_SEMITONES)
    ):
        if string_num == 0:
            start_fret = fret_start
        else:
            start_fret = _first_note_gte(
                open_semitone, scale_pitches[next_pitch_idx], min_fret_for_next
            )

        count = 0
        fret = start_fret
        last_pitch_idx: int | None = None

        while count < notes_per_string and fret <= start_fret + _MAX_EXTRA:
            pitch = (open_semitone + fret) % 12
            if pitch in pitch_to_interval:
                cells.append(
                    FretCell(
                        string_idx=string_idx,
                        fret=fret,
                        interval=pitch_to_interval[pitch],
                    )
                )
                count += 1
                if fret > max_fret:
                    max_fret = fret
                last_pitch_idx = scale_pitches.index(pitch)
            fret += 1

        if last_pitch_idx is not None:
            next_pitch_idx = (last_pitch_idx + 1) % len(scale_pitches)
            min_fret_for_next = max(0, start_fret - 3)

    return cells, max_fret


def degree_fret_start_with_shift(
    root: str,
    scale: Scale,
    degree: int,
    notes_per_string: int,
    threshold: int = 10,
) -> int:
    """Return the starting fret for a degree, shifting up by 12 if needed.

    When base_fret is 0 and projecting from there forces any higher string's
    first note to be >= ``threshold`` (default 10), the shape is shifted up
    by one octave (+12 frets) so it sits in a more compact, playable region
    of the neck.
    """
    base_fret = degree_fret_start(root, scale, degree)
    if base_fret == 0:
        cells, _ = project_scale_n_notes(root, scale, notes_per_string, base_fret)
        for i in range(1, 6):
            string_cells = [c for c in cells if c.string_idx == i]
            if string_cells:
                first_fret = min(c.fret for c in string_cells)
                if first_fret >= threshold:
                    return base_fret + 12
    return base_fret


def degree_fret_start(root: str, scale: Scale, degree: int) -> int:
    """Return the first fret (≥ 0) on the low E string where scale degree N occurs.

    degree: 1-indexed (1 = root, 2 = second scale degree, etc.)
    """
    if degree < 1 or degree > len(scale.intervals):
        raise ValueError(f"Degree {degree} out of range for a {len(scale.intervals)}-note scale")
    root_semitone = note_to_semitone(root)
    degree_semitone = (root_semitone + scale.semitones[degree - 1]) % 12
    open_e = _OPEN_SEMITONES[0]  # E = 4
    return (degree_semitone - open_e + 12) % 12

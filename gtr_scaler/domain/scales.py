"""Scale definitions, interval resolution, and mode computation."""

from dataclasses import dataclass, field

from .notes import note_to_semitone, semitone_to_note

# Interval symbol → semitones from root
INTERVAL_SEMITONES: dict[str, int] = {
    '1': 0,
    'm2': 1,  'M2': 2,
    'm3': 3,  'M3': 4,
    'P4': 5,  'A4': 6, 'd5': 6,
    'P5': 7,
    'm6': 8,  'M6': 9,
    'm7': 10, 'M7': 11,
}

# Canonical semitone → interval symbol (A4 preferred over d5 for tritone)
_SEMITONE_TO_INTERVAL: dict[int, str] = {
    0: '1',  1: 'm2', 2: 'M2', 3: 'm3', 4: 'M3',
    5: 'P4', 6: 'A4', 7: 'P5', 8: 'm6', 9: 'M6',
    10: 'm7', 11: 'M7',
}

SCALE_PATTERNS: dict[str, str] = {
    # Pentatonic
    'pentatonic_minor': '1 m3 P4 P5 m7',
    'pentatonic_major': '1 M2 M3 P5 M6',
    # Major scale modes
    'major':       '1 M2 M3 P4 P5 M6 M7',
    'ionian':      '1 M2 M3 P4 P5 M6 M7',
    'dorian':      '1 M2 m3 P4 P5 M6 m7',
    'phrygian':    '1 m2 m3 P4 P5 m6 m7',
    'lydian':      '1 M2 M3 A4 P5 M6 M7',
    'mixolydian':  '1 M2 M3 P4 P5 M6 m7',
    'aeolian':     '1 M2 m3 P4 P5 m6 m7',
    'locrian':     '1 m2 m3 P4 d5 m6 m7',
    # Minor variants
    'natural_minor':  '1 M2 m3 P4 P5 m6 m7',
    'harmonic_minor': '1 M2 m3 P4 P5 m6 M7',
    'melodic_minor':  '1 M2 m3 P4 P5 M6 M7',
    # Melodic minor modes
    'altered': '1 m2 m3 M3 A4 m6 m7',   # mode 7 of melodic minor (super-locrian)
    # Other
    'blues': '1 m3 P4 A4 P5 m7',
}

# Known mode names for the major scale (degree → name)
_MAJOR_MODE_NAMES: dict[int, str] = {
    1: 'Ionian', 2: 'Dorian', 3: 'Phrygian', 4: 'Lydian',
    5: 'Mixolydian', 6: 'Aeolian', 7: 'Locrian',
}

# Known mode names for the melodic minor scale (degree → name)
_MELODIC_MINOR_MODE_NAMES: dict[int, str] = {
    1: 'Melodic Minor',
    2: 'Dorian b2',
    3: 'Lydian Augmented',
    4: 'Lydian Dominant',
    5: 'Mixolydian b6',
    6: 'Locrian #2',
    7: 'Altered',
}

# Known mode names for the pentatonic scales (degree → name)
_PENTATONIC_MAJOR_MODE_NAMES: dict[int, str] = {
    1: 'Major Pentatonic',    # 1 M2 M3 P5 M6
    2: 'Egyptian',            # 1 M2 P4 P5 m7  (suspended pentatonic)
    3: 'Man Gong',            # 1 m3 P4 m6 m7
    4: 'Ritusen',             # 1 M2 P4 P5 M6
    5: 'Minor Pentatonic',    # 1 m3 P4 P5 m7
}


@dataclass(frozen=True)
class Scale:
    name: str
    intervals: tuple[str, ...]
    _display: str = field(default='', compare=False)

    @property
    def semitones(self) -> tuple[int, ...]:
        return tuple(INTERVAL_SEMITONES[i] for i in self.intervals)

    @property
    def display_name(self) -> str:
        return self._display or self.name.replace('_', ' ').title()


def get_scale(name: str) -> Scale:
    """Look up a built-in scale by name."""
    try:
        pattern = SCALE_PATTERNS[name]
    except KeyError:
        available = ', '.join(SCALE_PATTERNS)
        raise ValueError(f"Unknown scale {name!r}. Available: {available}") from None
    return Scale(name=name, intervals=tuple(pattern.split()))


def degree_root(root: str, scale: Scale, degree: int) -> str:
    """Return the note name of the Nth scale degree starting from *root* (1-indexed)."""
    n = len(scale.intervals)
    if not 1 <= degree <= n:
        raise ValueError(f"Degree {degree} out of range for a {n}-note scale (1–{n})")
    offset = scale.semitones[degree - 1]
    return semitone_to_note((note_to_semitone(root) + offset) % 12)


def compute_mode(scale: Scale, degree: int) -> Scale:
    """Return the Nth mode of *scale* (degree is 1-indexed).

    Rotates the interval pattern so that the Nth degree becomes the new root,
    then re-maps semitone offsets back to canonical interval symbols.
    """
    n = len(scale.intervals)
    if not 1 <= degree <= n:
        raise ValueError(f"Degree {degree} out of range for a {n}-note scale (1–{n})")
    if degree == 1:
        return scale

    semitones = scale.semitones
    pivot = semitones[degree - 1]
    # Rotate the list so degree N is first, then subtract the pivot
    rotated = tuple((semitones[(degree - 1 + i) % n] - pivot) % 12 for i in range(n))
    intervals = tuple(_SEMITONE_TO_INTERVAL[s] for s in rotated)

    # Build a human-readable display name
    parent_base = scale.name.split('_mode')[0]  # strip any previous mode suffix
    if parent_base in ('major', 'ionian') and degree in _MAJOR_MODE_NAMES:
        display = _MAJOR_MODE_NAMES[degree]
    elif parent_base == 'melodic_minor' and degree in _MELODIC_MINOR_MODE_NAMES:
        display = _MELODIC_MINOR_MODE_NAMES[degree]
    elif parent_base == 'pentatonic_major' and degree in _PENTATONIC_MAJOR_MODE_NAMES:
        display = _PENTATONIC_MAJOR_MODE_NAMES[degree]
    else:
        display = f"{scale.display_name} (mode {degree})"

    return Scale(
        name=f"{parent_base}_mode{degree}",
        intervals=intervals,
        _display=display,
    )

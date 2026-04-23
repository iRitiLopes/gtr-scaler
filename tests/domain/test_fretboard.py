from gtr_scaler.domain.fretboard import project_scale, project_scale_n_notes
from gtr_scaler.domain.scales import get_scale


def _cell_map(root: str, scale_name: str, fret_end: int = 12) -> dict[tuple[int, int], bool]:
    """Returns {(string_idx, fret): is_root} for all scale cells."""
    scale = get_scale(scale_name)
    return {(c.string_idx, c.fret): c.is_root for c in project_scale(root, scale, fret_end=fret_end)}


def test_a_minor_pentatonic_low_e_string():
    # Low E string (idx 0), open = E(4)
    # A minor pent notes: A C D E G  →  pitches 9, 0, 2, 4, 7
    cells = _cell_map('A', 'pentatonic_minor')
    assert (0, 0) in cells   # E — scale note
    assert (0, 3) in cells   # G — scale note
    assert (0, 5) in cells   # A — root
    assert cells[(0, 5)] is True  # must be root
    assert (0, 8) in cells   # C — scale note
    assert (0, 10) in cells  # D — scale note
    assert (0, 12) in cells  # E — scale note (octave)
    assert (0, 1) not in cells  # F# — not in scale


def test_a_minor_pentatonic_a_string():
    # A string (idx 1), open = A(9) → fret 0 is root
    cells = _cell_map('A', 'pentatonic_minor')
    assert cells[(1, 0)] is True   # A — root
    assert (1, 3) in cells          # C
    assert (1, 5) in cells          # D
    assert (1, 7) in cells          # E
    assert (1, 10) in cells         # G
    assert cells[(1, 12)] is True   # A — root again


def test_root_count_is_correct():
    scale = get_scale('pentatonic_minor')
    cells = project_scale('A', scale, fret_end=12)
    roots = [c for c in cells if c.is_root]
    assert len(roots) >= 6


def test_no_extra_notes_outside_scale():
    from gtr_scaler.domain.notes import note_to_semitone
    scale = get_scale('pentatonic_minor')
    root = 'A'
    root_st = note_to_semitone(root)
    scale_pitches = frozenset((root_st + s) % 12 for s in scale.semitones)
    from gtr_scaler.domain.fretboard import _OPEN_SEMITONES
    for c in project_scale(root, scale, fret_end=12):
        pitch = (_OPEN_SEMITONES[c.string_idx] + c.fret) % 12
        assert pitch in scale_pitches


def test_fret_range_start():
    # Only frets 5-9 should appear
    scale = get_scale('pentatonic_minor')
    cells = project_scale('A', scale, fret_start=5, fret_end=9)
    assert all(5 <= c.fret <= 9 for c in cells)
    assert any(c.fret == 5 for c in cells)


def test_fret_range_excludes_outside():
    scale = get_scale('pentatonic_minor')
    cells = project_scale('A', scale, fret_start=5, fret_end=9)
    assert not any(c.fret < 5 or c.fret > 9 for c in cells)


def test_a_minor_pentatonic_box1_position():
    # Box 1 position: strings 0-5, frets 5-8
    # E:5(A),8(C) | A:5(D),7(E) | D:5(G),7(A) | G:5(C),7(D) | B:5(E),8(G) | e:5(A),8(C)
    cells = _cell_map('A', 'pentatonic_minor')
    box1 = {
        0: [5, 8],
        1: [5, 7],
        2: [5, 7],
        3: [5, 7],
        4: [5, 8],
        5: [5, 8],
    }
    for string_idx, frets in box1.items():
        for fret in frets:
            assert (string_idx, fret) in cells, f"Expected (string={string_idx}, fret={fret}) in scale cells"


def test_a_minor_pentatonic_3_notes_per_string():
    # Traced manually: A minor pent (1 m3 P4 P5 m7), root A=9
    # scale_pitches = (9, 0, 2, 4, 7), open semitones = (4,9,2,7,11,4)
    scale = get_scale('pentatonic_minor')
    cells, fret_end = project_scale_n_notes('A', scale, notes_per_string=3)

    by_string: dict[int, list[int]] = {}
    for c in cells:
        by_string.setdefault(c.string_idx, []).append(c.fret)

    expected = {
        0: [0, 3, 5],    # E: P5(E) m7(G) 1(A)
        1: [3, 5, 7],    # A: m3(C) P4(D) P5(E)
        2: [5, 7, 10],   # D: m7(G) 1(A) m3(C)
        3: [7, 9, 12],   # G: P4(D) P5(E) m7(G)
        4: [10, 13, 15], # B: 1(A) m3(C) P4(D)
        5: [12, 15, 17], # e: P5(E) m7(G) 1(A)
    }
    for string_idx, frets in expected.items():
        assert by_string.get(string_idx) == frets, (
            f"String {string_idx}: got {by_string.get(string_idx)}, expected {frets}"
        )
    assert fret_end == 17


def test_a_minor_pentatonic_3_notes_per_string_fret_start_5():
    # Same as above but shifted: fret_start=5 lands on A (root) on low E
    # String 0 starts at fret 5 and picks up the scale from there
    scale = get_scale('pentatonic_minor')
    cells, fret_end = project_scale_n_notes('A', scale, notes_per_string=3, fret_start=5)

    by_string: dict[int, list[int]] = {}
    for c in cells:
        by_string.setdefault(c.string_idx, []).append(c.fret)

    expected = {
        0: [5, 8, 10],   # E: 1(A) m3(C) P4(D)
        1: [7, 10, 12],  # A: P5(E) m7(G) 1(A)
        2: [10, 12, 14], # D: m3(C) P4(D) P5(E)
        3: [12, 14, 17], # G: m7(G) 1(A) m3(C)
        4: [15, 17, 20], # B: P4(D) P5(E) m7(G)
        5: [17, 20, 22], # e: 1(A) m3(C) P4(D)
    }
    for string_idx, frets in expected.items():
        assert by_string.get(string_idx) == frets, (
            f"String {string_idx}: got {by_string.get(string_idx)}, expected {frets}"
        )
    assert fret_end == 22

# AGENTS.md — gtr-scaler

## Project Overview

`gtr-scaler` is a Python tool to generate and export guitar scale diagrams.
It targets two output formats (SVG/PDF and ASCII/text) and will eventually expose a local Flask HTTP
server so outputs can be previewed and downloaded from a browser.

**Current state:** ASCII viewer, SVG renderer, and PDF export are all working.
Flask server is not yet built.

---

## Agent Identity & Expertise

You are a **senior Python engineer with deep music theory knowledge**, specializing in:

- **Software engineering**: clean architecture, type annotations, idiomatic Python 3.11+,
  packaging (pyproject.toml), testing (pytest), and REST API design with Flask.
- **Music theory**: scales (major, minor, modes, pentatonic, blues, exotic), intervals,
  degrees, CAGED system, fretboard layout.
- **Guitar pedagogy**: how scales are typically visualized on a fretboard — positions,
  patterns, finger-friendly layouts, root highlighting.

When generating or reviewing code, apply both lenses simultaneously: correctness as an
engineer *and* musical accuracy as a guitarist.

---

## Domain Knowledge

### Fretboard model
- Tuning is fixed: standard — E2 A2 D3 G3 B3 E4 (low to high). No alternate tunings.
- String indices: 0 = low E, 5 = high e.
- Each cell is identified by `(string_index, fret_number)`.
- Notes wrap chromatically: C C# D D# E F F# G G# A A# B.
- Open-string semitone values (low→high): E=4, A=9, D=2, G=7, B=11, E=4.

### Scale representation

Scales are defined as a **root note** + an ordered list of **interval symbols** measured
from the root (not as step distances between consecutive notes).

#### Interval symbol notation

| Symbol | Name              | Semitones | Display label |
|--------|-------------------|-----------|---------------|
| `1`    | Unison (root)     | 0         | `R`           |
| `m2`   | Minor 2nd         | 1         | `b2`          |
| `M2`   | Major 2nd         | 2         | `2`           |
| `m3`   | Minor 3rd         | 3         | `b3`          |
| `M3`   | Major 3rd         | 4         | `3`           |
| `P4`   | Perfect 4th       | 5         | `4`           |
| `A4`   | Augmented 4th     | 6         | `#4`          |
| `d5`   | Diminished 5th    | 6         | `b5`          |
| `P5`   | Perfect 5th       | 7         | `5`           |
| `m6`   | Minor 6th         | 8         | `b6`          |
| `M6`   | Major 6th         | 9         | `6`           |
| `m7`   | Minor 7th         | 10        | `b7`          |
| `M7`   | Major 7th         | 11        | `7`           |

- `A4` and `d5` both resolve to semitone 6. **`A4` is the canonical spelling** for the
  reverse lookup (`_SEMITONE_TO_INTERVAL`).
- Display labels use the numeric shorthand (`b3`, `5`, `b7`), not the full symbol.

#### Built-in scale definitions (implemented)

| Key (CLI name)      | Display name        | Intervals                       |
|---------------------|---------------------|---------------------------------|
| `pentatonic_minor`  | Pentatonic Minor    | 1 m3 P4 P5 m7                  |
| `pentatonic_major`  | Pentatonic Major    | 1 M2 M3 P5 M6                  |
| `major`             | Major               | 1 M2 M3 P4 P5 M6 M7            |
| `ionian`            | Ionian              | 1 M2 M3 P4 P5 M6 M7            |
| `dorian`            | Dorian              | 1 M2 m3 P4 P5 M6 m7            |
| `phrygian`          | Phrygian            | 1 m2 m3 P4 P5 m6 m7            |
| `lydian`            | Lydian              | 1 M2 M3 A4 P5 M6 M7            |
| `mixolydian`        | Mixolydian          | 1 M2 M3 P4 P5 M6 m7            |
| `aeolian`           | Aeolian             | 1 M2 m3 P4 P5 m6 m7            |
| `locrian`           | Locrian             | 1 m2 m3 P4 d5 m6 m7            |
| `natural_minor`     | Natural Minor       | 1 M2 m3 P4 P5 m6 m7            |
| `harmonic_minor`    | Harmonic Minor      | 1 M2 m3 P4 P5 m6 M7            |
| `melodic_minor`     | Melodic Minor       | 1 M2 m3 P4 P5 M6 M7            |
| `altered`           | Altered             | 1 m2 m3 M3 A4 m6 m7            |
| `blues`             | Blues               | 1 m3 P4 A4 P5 m7               |

### Scale modes

A **mode** rotates a parent scale's interval pattern so that the Nth degree becomes the
new root. Both the **root** and the **intervals** must shift together.

**Correct semantics:** `C major --mode 6` means "6th degree of C major is A → show A Aeolian".
The root moves from C to A; the interval pattern rotates to Aeolian. The displayed root is A,
not C.

**Algorithm (`compute_mode`):**
1. Take parent semitone offsets: e.g. major = `[0, 2, 4, 5, 7, 9, 11]`
2. Rotate so degree N is first: `semitones[N-1:] + semitones[:N-1]`
3. Subtract the pivot (semitones[N-1]) mod 12 → new offsets start at 0
4. Map back via `_SEMITONE_TO_INTERVAL`

**New root computation (`degree_root`):**
```
new_root_semitone = (note_to_semitone(root) + scale.semitones[degree - 1]) % 12
```

#### Named mode lookup tables

Major scale modes:

| Degree | Name        |
|--------|-------------|
| 1      | Ionian      |
| 2      | Dorian      |
| 3      | Phrygian    |
| 4      | Lydian      |
| 5      | Mixolydian  |
| 6      | Aeolian     |
| 7      | Locrian     |

Melodic minor modes:

| Degree | Name               | Notes                                          |
|--------|--------------------|------------------------------------------------|
| 1      | Melodic Minor      |                                                |
| 2      | Dorian b2          |                                                |
| 3      | Lydian Augmented   |                                                |
| 4      | Lydian Dominant    |                                                |
| 5      | Mixolydian b6      |                                                |
| 6      | Locrian #2         |                                                |
| 7      | Altered            | Same as the `altered` scale; all tensions altered |

The `altered` scale is also available directly by name (equivalent to melodic minor mode 7).
Example: `F altered` = `F# melodic_minor --mode 7`.

Major pentatonic modes:

| Degree | Name             | Intervals        |
|--------|------------------|------------------|
| 1      | Major Pentatonic | 1 M2 M3 P5 M6   |
| 2      | Egyptian         | 1 M2 P4 P5 m7   |
| 3      | Man Gong         | 1 m3 P4 m6 m7   |
| 4      | Ritusen          | 1 M2 P4 P5 M6   |
| 5      | Minor Pentatonic | 1 m3 P4 P5 m7   |

Mode 5 of major pentatonic = minor pentatonic (classic relationship).

### FretCell — the core value object

```python
@dataclass(frozen=True)
class FretCell:
    string_idx: int   # 0 = low E, 5 = high e
    fret: int
    interval: str     # interval symbol, e.g. '1', 'm3', 'P5'

    @property
    def is_root(self) -> bool:
        return self.interval == '1'
```

### Tetrad detection

Tetrad intervals (root, 3rd, 5th, 7th) for color/visual distinction:

```python
_TETRAD_INTERVALS = frozenset({'1', 'm3', 'M3', 'd5', 'A4', 'P5', 'm7', 'M7'})
```

Non-tetrad notes (e.g. P4 in minor pentatonic) are "passing tones" and receive
a different visual treatment.

### Fret range

`project_scale` and `render` both accept `fret_start: int` and `fret_end: int` (inclusive).
Default: 0–12.

The CLI `--frets` argument accepts two formats:
- `--frets 22` → fret_start=0, fret_end=22
- `--frets 5-9` → fret_start=5, fret_end=9

### Notes-per-string projection

`project_scale_n_notes(root, scale, notes_per_string, fret_start)` implements
**horizontal position training**: the scale runs continuously across all 6 strings.

**Key rules:**
- Each string shows exactly `notes_per_string` scale notes.
- The scale flows continuously: each string picks up the **next scale degree** after where
  the previous string ended — the same note is never repeated as both the last of one
  string and the first of the next.
- Each new string's opening note is found at the first occurrence that is no more than
  **3 frets behind** the previous string's starting fret (allows natural position shifts
  without jumping a full octave higher).
- `fret_end` is computed dynamically as the highest fret used across all strings.
- Mutually exclusive with `--frets` in the CLI.

**Helper:** `_first_note_gte(open_semitone, target_pitch, min_fret) -> int`
Returns the first fret ≥ min_fret on a given string where `target_pitch` (mod 12) occurs.

### Starting degree

`degree_fret_start(root, scale, degree) -> int` returns the first fret (≥ 0) on the
**low E string** where scale degree N occurs.

- Always used when `--notes` is active (even for degree 1), so the pattern is anchored
  to the chosen degree rather than to fret 0 (which may not be a scale note).
- Only used when `--start-degree != 1` in `--frets` mode.

---

### Output formats

#### ASCII/Text (implemented)

Terminal-friendly grid:
- Strings displayed high e (top) → low E (bottom).
- Each cell is 4 characters wide between `|` bars: `-b3-`, `-R--`, `----`.
  - 1-char labels: `-R--`, `-5--`, `-4--`
  - 2-char labels: `-b3-`, `-b7-`, `#4-` → pad right with `-` to fill to 4.
- Fret numbers shown as a header row, right-aligned in 5-char slots.
- A legend line below the diagram lists only the interval symbols present in that scale,
  e.g. `R=1   b3=m3   4=P4   5=P5   b7=m7`.

**ANSI color** (auto-detected via `sys.stdout.isatty()`; overridable with `color: bool`):

| Note type       | Color              | ANSI code    |
|-----------------|--------------------|--------------|
| Root (`1`)      | Bold bright red    | `\033[1;91m` |
| Tetrad tones    | Bold bright green  | `\033[1;92m` |
| Passing tones   | Yellow             | `\033[0;33m` |

Only the label text is wrapped in ANSI codes; the surrounding dashes are plain,
so column alignment is preserved regardless of color mode.

#### SVG / PDF (implemented)

Uses the `fretboard` library (wraps `svgwrite`) to render a visual diagram with filled
circles on each scale note, color-coded by interval type.

**Color scheme (SVG/PDF):**

| Note type    | Color       |
|--------------|-------------|
| Root (`1`)   | `firebrick` |
| Tetrad tones | `steelblue` |
| Passing tones| `olivedrab` |

**Orientation:** the diagram is **rotated 90° counter-clockwise** from the library default,
so frets run left→right and strings run bottom (low E) → top (high e) — the standard
orientation for printed scale sheets.

**Diagram height** auto-scales: `fret_space = 44px` per fret so markers (radius 14) never
overlap, regardless of how many frets are shown.

**PDF** is generated by converting the SVG via `cairosvg`.

**Compatibility note:** `fretboard==1.0.0` depends on `attrdict` and `pyyaml` versions that
use removed `collections.*` ABCs. `renderers/svg.py` patches these at import time before
loading the library:
```python
for _name in ("Mapping", "MutableMapping", "Sequence", "Hashable"):
    if not hasattr(collections, _name):
        setattr(collections, _name, getattr(collections.abc, _name))
```

---

## Tech Stack

| Layer        | Choice              | Notes                                          |
|--------------|---------------------|------------------------------------------------|
| Language     | Python 3.11+        | Use `match`, walrus, `TypeAlias`, etc.         |
| CLI          | `argparse` (stdlib) | Entry point is `gtr_scaler/__main__.py`        |
| Web server   | Flask               | Not yet built — future layer                   |
| SVG          | `fretboard` + `svgwrite` | Diagram rendering                         |
| PDF          | `cairosvg`          | SVG → PDF conversion                           |
| Testing      | `pytest`            | Unit + integration, no mocks of core logic     |
| Packaging    | `pyproject.toml`    | PEP 517/518, hatchling backend                 |
| Dep manager  | `uv`                | Use `uv add`, `uv run`, `uv sync`; lock file committed |

---

## Architecture

```
gtr_scaler/
├── domain/          # Pure music logic — no I/O, no Flask
│   ├── notes.py     # Chromatic scale, enharmonics, pitch math
│   ├── scales.py    # Scale definitions, mode computation
│   └── fretboard.py # Fretboard model, scale projection → FretCell list
├── renderers/       # Output generation — depends on domain only
│   ├── ascii.py     # Terminal renderer (ANSI color, degree labels)
│   └── svg.py       # SVG/PDF renderer via fretboard + cairosvg
├── server/          # Flask app — not yet built
│   ├── app.py
│   └── routes.py
└── __main__.py      # argparse CLI entry point
```

**Rules:**
- `domain/` must have **zero** dependencies on Flask, cairosvg, or any I/O library.
- `renderers/` depends on `domain/` but never on `server/`.
- `server/` only orchestrates: parse request → call domain → call renderer → return response.
- Keep functions small and pure where possible; prefer immutable data structures.

### Key domain functions

| Function | Signature | Purpose |
|----------|-----------|---------|
| `note_to_semitone` | `(note: str) -> int` | Parse note name (sharps + flats) to 0–11 |
| `semitone_to_note` | `(semitone: int) -> str` | Canonical sharp spelling |
| `get_scale` | `(name: str) -> Scale` | Look up built-in scale by key |
| `compute_mode` | `(scale, degree) -> Scale` | Rotate intervals to Nth mode |
| `degree_root` | `(root, scale, degree) -> str` | Find the note name of the Nth degree |
| `project_scale` | `(root, scale, fret_start, fret_end) -> list[FretCell]` | Full projection |
| `project_scale_n_notes` | `(root, scale, notes_per_string, fret_start) -> tuple[list[FretCell], int]` | N-notes-per-string projection; returns cells + computed fret_end |
| `degree_fret_start` | `(root, scale, degree) -> int` | First fret on low E string where degree N occurs |

---

## CLI Interface

```
python -m gtr_scaler [root] [scale] [--frets N|START-END | --notes N]
                     [--mode N] [--start-degree N] [--output FILE]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `root` | `A` | Root note (e.g. `C`, `F#`, `Bb`) |
| `scale` | `pentatonic_minor` | Scale key from `SCALE_PATTERNS` |
| `--frets` | `12` | Fret range: `22` (0–22) or `5-9` (5–9 only). Mutually exclusive with `--notes`. |
| `--notes` | — | N notes per string, scale flowing continuously across strings. Mutually exclusive with `--frets`. |
| `--mode` | `1` | Mode degree (shifts root to Nth degree of parent scale) |
| `--start-degree` | `1` | Scale degree to anchor on the low E string. With `--notes`, always applied (including degree 1). With `--frets`, only applied when ≠ 1. |
| `--output` | — | Export to file. Extension determines format: `.svg` or `.pdf`. Omit to print ASCII to stdout. |

Examples:
```bash
python -m gtr_scaler                                          # A minor pentatonic, frets 0-12
python -m gtr_scaler A pentatonic_minor --frets 5-9           # box position at 5th fret
python -m gtr_scaler A pentatonic_minor --frets 22            # full 22-fret neck
python -m gtr_scaler C major --mode 2                         # D Dorian
python -m gtr_scaler C major --mode 6                         # A Aeolian
python -m gtr_scaler C pentatonic_major --mode 5              # A Minor Pentatonic
python -m gtr_scaler A dorian                                 # A Dorian directly by name
python -m gtr_scaler A pentatonic_minor --notes 3             # 3 notes/string from root
python -m gtr_scaler C pentatonic_major --notes 3 --start-degree 3  # start from 3rd degree (E)
python -m gtr_scaler F# melodic_minor --mode 7 --notes 3 --start-degree 3
python -m gtr_scaler F altered                                # F altered scale (= F# mel.min. mode 7)
python -m gtr_scaler A pentatonic_minor --output scale.svg    # export SVG
python -m gtr_scaler A pentatonic_minor --notes 3 --output scale.pdf  # export PDF
```

---

## Coding Standards

- Full type annotations on all public functions and classes.
- `dataclass(frozen=True)` for domain value objects (`Scale`, `FretCell`).
- `Scale._display` is an optional override for `display_name`; used by `compute_mode` to
  inject named mode strings (e.g. "Dorian") without mangling the `name` field.
- No bare `except:` — always catch specific exceptions.
- Prefer `pathlib.Path` over `os.path`.
- Format with `ruff` (line length 100); lint with `ruff check`.
- Tests live in `tests/` mirroring the `gtr_scaler/` structure.
- Every domain function must have at least one unit test.

---

## Flask Server (future)

- Base URL: `http://localhost:5000`
- Routes return either JSON (for data) or a binary file response (for PDF/ASCII download).
- Use `Flask` blueprints if routes grow beyond ~5 endpoints.
- No template rendering — API server only.
- Error responses: `{"error": "<message>"}` with appropriate HTTP status codes.

### Planned endpoints

- `GET /scales` — list available scale names
- `GET /scales/<name>?root=<note>&frets=<range>&mode=<n>` — fretboard data as JSON
- `GET /export/ascii?...` — return plain text
- `GET /export/svg?...` — return SVG file
- `GET /export/pdf?...` — return PDF file

Query parameters:

| Parameter      | Type   | Default  | Description                                               |
|----------------|--------|----------|-----------------------------------------------------------|
| `root`         | string | `A`      | Root note (e.g. `C`, `F#`, `Bb`)                         |
| `frets`        | string | `12`     | Fret range: `22` or `5-9`. Mutually exclusive with `nps`. |
| `mode`         | int    | `1`      | Mode degree                                               |
| `nps`          | int    | —        | Notes-per-string; mutually exclusive with `frets`         |
| `start_degree` | int    | `1`      | Scale degree to anchor on low E string                    |

Passing both `nps` and `frets` (as a range) must return HTTP 400.

---

## Musical Accuracy Rules

- Enharmonic flats are normalized to sharps internally (e.g. `Bb` → `A#`, `Eb` → `D#`).
- When projecting a scale to the fretboard, always include **all positions across all strings**
  within the requested fret range unless a projection filter (nps) is applied.
- **Mode = root shift + interval rotation.** Never rotate intervals without also moving the root
  to the Nth degree of the parent scale.
- The root degree must always be visually distinguished regardless of rendering context.
- The **altered scale** is the 7th mode of the melodic minor scale. It contains all altered
  tensions (b9, #9, #11, b13) and is used over dominant 7th chords resolving a half-step up.

---

## Out of Scope (for now)

- Audio playback or MIDI generation
- User authentication
- Database persistence
- Frontend JavaScript framework — plain HTTP responses only
- Alternate tunings

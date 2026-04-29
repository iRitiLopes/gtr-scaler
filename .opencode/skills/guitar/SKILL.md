---
name: gtr-scaler
description: Generate guitar scale diagrams using the gtr-scaler project
tags: [music, guitar, scales, diagrams]
---

# gtr-scaler Skill

## Purpose
Use the `gtr-scaler` Python project to generate and export guitar scale
fretboard diagrams in ASCII, SVG, or PDF formats.

## When to use
- The user asks for guitar scale diagrams, fretboard patterns, or scale
  shapes.
- The user wants to print or export scale diagrams.
- The user mentions CAGED system, scale positions, notes-per-string, or
  modes.

## Available scales
The project knows these built-in scales:
- pentatonic_minor, pentatonic_major
- major, ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian
- natural_minor, harmonic_minor, melodic_minor
- altered, blues

## CLI Quick Reference

### Basic usage
```bash
python -m gtr_scaler [root] [scale] [options]
```

### Common workflows

**1. Single scale diagram (ASCII to terminal)**
```bash
python -m gtr_scaler A pentatonic_minor
```

**2. Single scale diagram (export to file)**
```bash
python -m gtr_scaler A pentatonic_minor --output scale.svg
python -m gtr_scaler A pentatonic_minor --output scale.pdf
```

**3. All scale shapes (CAGED-style positions)**
```bash
python -m gtr_scaler A pentatonic_minor --all-degrees --notes 3
python -m gtr_scaler C major --all-degrees --notes 3 --output all_shapes.pdf
```
- `--all-degrees` generates one diagram per scale degree.
- `--notes` (2-4) sets notes per string.
- PDF output is paginated with max 3 diagrams per page.

**4. Modes**
```bash
python -m gtr_scaler C major --mode 2          # D Dorian
python -m gtr_scaler C major --mode 6          # A Aeolian
```

**5. Notes-per-string (horizontal positions)**
```bash
python -m gtr_scaler A pentatonic_minor --notes 3
python -m gtr_scaler C major --notes 2 --start-degree 3
```

**6. Fixed fret range**
```bash
python -m gtr_scaler A pentatonic_minor --frets 5-9
python -m gtr_scaler A pentatonic_minor --frets 22
```

## Agent workflow
1. **Parse user intent**: Determine root note, scale, output format, and
   whether they want all shapes or a single diagram.
2. **Build the CLI command**: Use the patterns above.
3. **Execute**: Run `python -m gtr_scaler ...` via subprocess.
4. **Handle output**:
   - ASCII: stream to stdout; summarize what was generated.
   - SVG/PDF: file path is printed as `Saved: {path}`; confirm the file
     exists.
5. **Musical guidance**: If the user is unsure, suggest common scales
   (pentatonic minor/major for beginners, major modes for intermediate).

## Constraints
- Always validate that `--all-degrees` has `--notes` between 2-4.
- `--all-degrees` and `--start-degree` are mutually exclusive.
- `--notes` and `--frets` are mutually exclusive.
- Output formats are determined by file extension: `.svg` or `.pdf`.

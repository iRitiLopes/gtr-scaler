# gtr-scaler

A Python CLI tool to generate and export guitar scale diagrams as ASCII, SVG, or PDF.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![uv](https://img.shields.io/badge/dep--manager-uv-DE5FE9)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC)
![fretboard](https://img.shields.io/badge/svg-fretboard--1.0.0-orange)
![cairosvg](https://img.shields.io/badge/pdf-cairosvg--2.7+-green)

## Installation

### Install uv

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and sync

```bash
git clone <repository-url>
cd gtr-scaler
uv sync --group dev
```

## Usage

```bash
# A minor pentatonic, frets 0-12 (default)
uv run python -m gtr_scaler

# Shorthand (uses the project.scripts entry point)
uv run gtr-scaler

# E major pentatonic
uv run python -m gtr_scaler E pentatonic_major

# Box position at frets 5-9
uv run python -m gtr_scaler A pentatonic_minor --frets 5-9

# Full 22-fret neck
uv run python -m gtr_scaler A pentatonic_minor --frets 22

# D Dorian (2nd mode of C major)
uv run python -m gtr_scaler C major --mode 2

# A Aeolian (6th mode of C major)
uv run python -m gtr_scaler C major --mode 6

# 3 notes per string, continuous flow
uv run python -m gtr_scaler C pentatonic_major --notes 3

# Start from the 3rd degree on the low E string
uv run python -m gtr_scaler C pentatonic_major --notes 3 --start-degree 3

# Export to SVG
uv run python -m gtr_scaler A pentatonic_minor --output scale.svg

# Export to PDF
uv run python -m gtr_scaler A pentatonic_minor --output scale.pdf

# Export all shapes to PDF
uv run python -m gtr_scaler F melodic_minor --notes 3 --all-degrees --output F_mel_min.pdf

# Export all shapes 4 per strings to PDF
uv run python -m gtr_scaler F altered --notes 4 --all-degrees --output F_alt_all_4str.pdf
```

## Examples

### ASCII output

```bash
$ uv run python -m gtr_scaler A pentatonic_minor --frets 5-9
```

```
A Pentatonic Minor  |  Standard tuning (E A D G B e)

       5    6    7    8    9
e  |-R--|----|----|-b3-|----|
B  |-5--|----|----|-b7-|----|
G  |-b3-|----|-4--|----|-5--|
D  |-b7-|----|-R--|----|----|
A  |-4--|----|-5--|----|----|
E  |-R--|----|----|-b3-|----|

  R=1   b3=m3   4=P4   5=P5   b7=m7
```

### Mode + notes-per-string

```bash
$ uv run python -m gtr_scaler C major --mode 2 --notes 3
```

```
D Dorian  |  Standard tuning (E A D G B e)

      10   11   12   13   14   15
e  |----|----|-2--|-b3-|----|-4--|
B  |----|----|-6--|-b7-|----|-R--|
G  |-b3-|----|-4--|----|-5--|----|
D  |-b7-|----|-R--|----|-2--|----|
A  |-4--|----|-5--|----|-6--|----|
E  |-R--|----|-2--|-b3-|----|----|

  R=1   2=M2   b3=m3   4=P4   5=P5   6=M6   b7=m7
```

### All degrees (CAGED shapes)

```bash
$ uv run python -m gtr_scaler A pentatonic_minor --notes 3 --all-degrees
```

Outputs 5 diagrams (one per scale degree), each with its own "Shape N" title.

### SVG export

```bash
$ uv run python -m gtr_scaler A pentatonic_minor --output scale.svg
```

Produces a landscape-oriented SVG with colored markers:
- **Red** = Root
- **Steel blue** = Tetrad tones (3rd, 5th, 7th)
- **Olive** = Passing tones

### PDF export (multi-page for all-degrees)

```bash
$ uv run python -m gtr_scaler C major --notes 3 --all-degrees --output shapes.pdf
```

Generates a multi-page PDF with up to 3 diagrams per page.

## Web Server

Run the Flask server to preview scales in a browser:

```bash
# Accessible from any device on your local network (default)
uv run gtr-scaler-server

# Custom port
uv run gtr-scaler-server --port 8080

# Localhost only
uv run gtr-scaler-server --host 127.0.0.1
```

The HTML frontend features interactive circular note buttons and colored scale
pill buttons. The diagram auto-updates as you select different options.

## Development

Run the test suite:

```bash
uv run pytest
```

Add a new dependency:

```bash
uv add <package>
```

Format and lint:

```bash
uv run ruff format .
uv run ruff check .
```

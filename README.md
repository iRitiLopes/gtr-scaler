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
```

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

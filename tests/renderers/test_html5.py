"""Tests for the HTML5 fretboard renderer."""

from __future__ import annotations

import re

from gtr_scaler.domain.fretboard import FretboardProjector
from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import ScaleCatalog
from gtr_scaler.renderers._constants import _INTERVAL_LABEL
from gtr_scaler.renderers.html5 import _INTERVAL_FULL_NAME, Html5Renderer

notes = NoteService()
catalog = ScaleCatalog(notes)
projector = FretboardProjector(notes)
renderer = Html5Renderer(projector)


def test_render_basic():
    """Render returns a string containing .gtr-diagram, <style>, and <script>."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    assert isinstance(result, str)
    assert ".gtr-diagram" in result
    assert "<style>" in result
    assert "<script>" in result


def test_render_has_title():
    """Title appears in an <h4> tag, properly escaped."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, title="A Pentatonic Minor — Shape 1")
    assert "<h4>" in result
    assert "A Pentatonic Minor" in result
    assert "Shape 1" in result
    assert "—" in result


def test_render_root_markers():
    """Root notes have the gtr-marker--root class."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    assert "gtr-marker--root" in result


def test_render_tetrad_markers():
    """Tetrad notes have the gtr-marker--tetrad class."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    # pentatonic minor has m3, P4, P5, m7 — m3, P5, m7 are tetrad
    assert "gtr-marker--tetrad" in result


def test_render_passing_markers():
    """Passing notes have the gtr-marker--passing class."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    # P4 is a passing tone in pentatonic minor
    assert "gtr-marker--passing" in result


def test_render_grid_structure():
    """Grid has correct number of rows and columns."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, fret_start=0, fret_end=5)
    # frets 0-5 = 6 frets
    assert "repeat(6, 50px)" in result
    # 6 strings
    assert "repeat(6, 40px)" in result


def test_render_string_labels():
    """String names appear: e at top, E at bottom."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    # Extract all string labels from the grid
    labels = re.findall(r'gtr-label">(.*?)</div>', result)
    # First label is empty (header corner), then e, B, G, D, A, E
    assert "e" in labels
    assert "E" in labels
    # e should appear before E (high e at top)
    e_idx = labels.index("e")
    E_idx = labels.index("E")
    assert e_idx < E_idx


def test_render_fret_numbers():
    """Fret numbers appear in the header row."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, fret_start=0, fret_end=5)
    for fret in range(0, 6):
        assert f'gtr-fret-num">{fret}</div>' in result


def test_render_legend():
    """Legend has entries only for intervals present in the scale."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    # pentatonic minor: 1, m3, P4, P5, m7
    assert "R=1" in result
    assert "b3=m3" in result
    assert "4=P4" in result
    assert "5=P5" in result
    assert "b7=m7" in result
    # These should NOT be in the legend
    assert "2=M2" not in result
    assert "3=M3" not in result
    assert "7=M7" not in result


def test_render_data_attributes():
    """Markers have data-interval-full attributes with full interval names."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    assert 'data-interval-full="Root"' in result
    assert 'data-interval-full="Minor 3rd"' in result
    assert 'data-interval-full="Perfect 4th"' in result
    assert 'data-interval-full="Perfect 5th"' in result
    assert 'data-interval-full="Minor 7th"' in result


def test_render_notes_per_string():
    """NPS mode works and produces markers."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, notes_per_string=3)
    assert "gtr-marker" in result
    # Should have root markers
    assert "gtr-marker--root" in result


def test_render_xss_title():
    """Title with <script> is escaped, not injected as HTML."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, title='<script>alert("xss")</script>')
    # The script tag should be escaped
    assert "<script>alert" not in result.replace("</script>", "").replace("<script>", "")
    assert "&lt;script&gt;" in result


def test_render_interval_full_names():
    """_INTERVAL_FULL_NAME covers all interval symbols in _INTERVAL_LABEL."""
    for symbol in _INTERVAL_LABEL:
        assert symbol in _INTERVAL_FULL_NAME, f"Missing full name for interval {symbol!r}"


def test_render_default_title():
    """When no title is provided, uses root + display_name."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale)
    assert "<h4>A Pentatonic Minor</h4>" in result


def test_render_fret_range():
    """Fret range is respected in the grid."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, fret_start=5, fret_end=9)
    # Should have fret numbers 5-9
    for fret in range(5, 10):
        assert f">{fret}<" in result
    # Should not have fret 0
    assert ">0<" not in result


def test_render_nut_class():
    """First fret column has the gtr-nut class."""
    scale = catalog.get("pentatonic_minor")
    result = renderer.render("A", scale, fret_start=0, fret_end=5)
    assert "gtr-nut" in result

import subprocess
import sys

import pytest


def test_cli_all_degrees_ascii():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Minor pentatonic has 5 intervals → 5 diagrams each with the header
    assert result.stdout.count("A Pentatonic Minor") == 5
    # Blank line separator between diagrams
    assert "\n\n" in result.stdout


def test_cli_all_degrees_requires_notes():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "all_degrees requires nps" in result.stderr


def test_cli_all_degrees_notes_out_of_range():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "5"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "between 2 and 4" in result.stderr


def test_cli_all_degrees_svg_output(tmp_path):
    out = tmp_path / "out.svg"
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3", "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "</svg>" in content


def test_cli_all_degrees_boundary_notes_2():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "2"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.count("A Pentatonic Minor") == 5


def test_cli_all_degrees_boundary_notes_4():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "4"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.count("A Pentatonic Minor") == 5


def test_cli_all_degrees_major_scale():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "C", "major",
         "--all-degrees", "--notes", "3"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # Major has 7 intervals -> 7 diagrams
    assert result.stdout.count("C Major") == 7


def test_cli_all_degrees_with_mode():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "C", "major",
         "--mode", "2", "--all-degrees", "--notes", "3"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # Dorian has 7 intervals -> 7 diagrams, root is D
    assert result.stdout.count("D Dorian") == 7


def test_cli_all_degrees_pdf_output(tmp_path):
    out = tmp_path / "out.pdf"
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3", "--output", str(out)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and "cairo" in result.stderr.lower():
        pytest.skip("Cairo native library not available")
    assert result.returncode == 0
    assert out.exists()
    # PDF files start with %PDF
    assert out.read_bytes().startswith(b"%PDF")


def test_cli_all_degrees_start_degree_conflict():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3", "--start-degree", "2"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "all_degrees cannot be used with start_degree" in result.stderr


def test_cli_all_degrees_ascii_shape_label():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    for deg in range(1, 6):
        assert f"Shape {deg}" in result.stdout


def test_cli_all_degrees_svg_has_shape_titles(tmp_path):
    out = tmp_path / "shapes.svg"
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3", "--output", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    content = out.read_text(encoding="utf-8")
    for deg in range(1, 6):
        assert f"Shape {deg}" in content


def _cairo_available() -> bool:
    """Check if cairosvg can actually be imported (native lib present)."""
    try:
        import cairosvg  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


def test_cli_all_degrees_pdf_page_count(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    out = tmp_path / "shapes.pdf"
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--all-degrees", "--notes", "3", "--output", str(out)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 and "cairo" in result.stderr.lower():
        pytest.skip("Cairo native library not available")
    assert result.returncode == 0
    reader = PdfReader(str(out))
    # 5 diagrams with max_per_page=3 → 2 pages
    assert len(reader.pages) == 2


def test_cli_all_degrees_major_pdf_page_count(tmp_path):
    if not _cairo_available():
        pytest.skip("Cairo native library not available")
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    out = tmp_path / "major_shapes.pdf"
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "C", "major",
         "--all-degrees", "--notes", "3", "--output", str(out)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 and "cairo" in result.stderr.lower():
        pytest.skip("Cairo native library not available")
    assert result.returncode == 0
    reader = PdfReader(str(out))
    # 7 diagrams with max_per_page=3 → 3 pages
    assert len(reader.pages) == 3


def test_cli_single_svg_has_title(tmp_path):
    out = tmp_path / "single.svg"
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "A", "pentatonic_minor",
         "--output", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    content = out.read_text(encoding="utf-8")
    assert "A Pentatonic Minor" in content
    assert "<text" in content


def test_cli_all_degrees_shift_to_12():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "E", "pentatonic_major",
         "--all-degrees", "--notes", "2"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # E major pentatonic degree 1 starts at fret 0 but shifts to 12
    # because string 1 starts at fret 11 (>= threshold 10).
    # The ASCII header for shape 1 should show frets starting at 12.
    assert "12   13   14" in result.stdout


def test_cli_all_degrees_no_unnecessary_shift():
    result = subprocess.run(
        [sys.executable, "-m", "gtr_scaler", "C", "major",
         "--all-degrees", "--notes", "3"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # C major degree 3 starts at fret 0 and stays compact (all strings
    # start at 0 or 1). The header for shape 3 should show frets 0-5.
    assert "    0    1    2    3    4    5" in result.stdout

"""Tests for the Flask web server routes."""

from __future__ import annotations

import pytest

from gtr_scaler.server.app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _cairo_available() -> bool:
    """Check if cairosvg can actually be imported (native lib present)."""
    try:
        import cairosvg  # noqa: F401

        return True
    except (ImportError, OSError):
        return False


# ── /scales ───────────────────────────────────────────────────────────────────


def test_list_scales(client):
    resp = client.get("/scales")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    keys = [s["key"] for s in data]
    assert "pentatonic_minor" in keys
    assert "major" in keys
    # Each entry has key and display
    for entry in data:
        assert "key" in entry
        assert "display" in entry


# ── /scales/<name> ────────────────────────────────────────────────────────────


def test_get_scale_data_default(client):
    resp = client.get("/scales/pentatonic_minor")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["root"] == "A"
    assert data["scale"]["name"] == "pentatonic_minor"
    assert data["scale"]["display_name"] == "Pentatonic Minor"
    assert data["fret_start"] == 0
    assert data["fret_end"] == 12
    assert data["mode"] == 1
    assert data["start_degree"] == 1
    assert data["notes_per_string"] is None
    assert isinstance(data["cells"], list)
    assert len(data["cells"]) > 0
    assert isinstance(data["interval_labels"], dict)
    # Every cell has expected keys
    for cell in data["cells"]:
        assert "string_idx" in cell
        assert "fret" in cell
        assert "interval" in cell
        assert "label" in cell
        assert "is_root" in cell


def test_get_scale_data_with_root(client):
    resp = client.get("/scales/major?root=C")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["root"] == "C"


def test_get_scale_data_with_mode(client):
    # C major mode 6 = A Aeolian
    resp = client.get("/scales/major?root=C&mode=6")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["root"] == "A"
    assert "Aeolian" in data["scale"]["display_name"]
    assert data["mode"] == 6


def test_get_scale_data_with_nps(client):
    resp = client.get("/scales/pentatonic_minor?nps=3")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["notes_per_string"] == 3
    # fret_end should be > 12 for 3-note patterns typically
    assert data["fret_end"] >= 0


def test_get_scale_data_invalid_root(client):
    resp = client.get("/scales/major?root=Z")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_get_scale_data_unknown_scale(client):
    resp = client.get("/scales/does_not_exist")
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data


def test_get_scale_data_invalid_mode(client):
    resp = client.get("/scales/major?mode=99")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_get_scale_data_bad_frets(client):
    resp = client.get("/scales/major?frets=abc")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


# ── /export/ascii ─────────────────────────────────────────────────────────────


def test_export_ascii(client):
    resp = client.get("/export/ascii?root=A&scale=pentatonic_minor")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/plain")
    text = resp.data.decode("utf-8")
    assert "-R--" in text
    assert "Pentatonic Minor" in text


def test_export_ascii_with_nps(client):
    resp = client.get("/export/ascii?root=A&scale=pentatonic_minor&nps=3")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "-R--" in text


# ── /export/svg ───────────────────────────────────────────────────────────────


def test_export_svg(client):
    resp = client.get("/export/svg?root=A&scale=pentatonic_minor")
    assert resp.status_code == 200
    assert resp.content_type.startswith("image/svg+xml")
    svg = resp.data.decode("utf-8")
    assert "<svg" in svg
    assert "</svg>" in svg


def test_export_svg_all_degrees(client):
    resp = client.get("/export/svg?root=A&scale=pentatonic_minor&all_degrees=1&nps=3")
    assert resp.status_code == 200
    svg = resp.data.decode("utf-8")
    assert "<svg" in svg
    # Should contain shape titles for all 5 pentatonic degrees
    for deg in range(1, 6):
        assert f"Shape {deg}" in svg


def test_export_svg_all_degrees_major(client):
    resp = client.get("/export/svg?root=C&scale=major&all_degrees=1&nps=3")
    assert resp.status_code == 200
    svg = resp.data.decode("utf-8")
    for deg in range(1, 8):
        assert f"Shape {deg}" in svg


def test_export_svg_with_mode(client):
    resp = client.get("/export/svg?root=C&scale=major&mode=6")
    assert resp.status_code == 200
    svg = resp.data.decode("utf-8")
    assert "Aeolian" in svg


# ── /export/pdf ───────────────────────────────────────────────────────────────


@pytest.mark.skipif(not _cairo_available(), reason="Cairo native library not available")
def test_export_pdf(client):
    resp = client.get("/export/pdf?root=A&scale=pentatonic_minor")
    assert resp.status_code == 200
    assert resp.content_type.startswith("application/pdf")
    assert resp.data.startswith(b"%PDF")


@pytest.mark.skipif(not _cairo_available(), reason="Cairo native library not available")
def test_export_pdf_all_degrees(client):
    resp = client.get("/export/pdf?root=A&scale=pentatonic_minor&all_degrees=1&nps=3")
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF")


# ── Validation edge cases ─────────────────────────────────────────────────────


def test_mutual_exclusion_frets_range_and_nps(client):
    resp = client.get("/scales/major?frets=5-9&nps=3")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "Cannot specify both" in data["error"]


def test_all_degrees_requires_nps(client):
    resp = client.get("/export/svg?root=A&scale=pentatonic_minor&all_degrees=1")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "nps" in data["error"].lower() or "2 and 4" in data["error"]


def test_all_degrees_nps_out_of_range(client):
    resp = client.get("/export/svg?root=A&scale=pentatonic_minor&all_degrees=1&nps=5")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "between 2 and 4" in data["error"]


def test_all_degrees_no_start_degree(client):
    resp = client.get(
        "/export/svg?root=A&scale=pentatonic_minor&all_degrees=1&nps=3&start_degree=2"
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "start_degree" in data["error"].lower() or "cannot" in data["error"].lower()


def test_invalid_nps_value(client):
    resp = client.get("/scales/major?nps=abc")
    assert resp.status_code == 400


def test_nps_zero(client):
    resp = client.get("/scales/major?nps=0")
    assert resp.status_code == 400


def test_negative_frets(client):
    resp = client.get("/scales/major?frets=-1")
    assert resp.status_code == 400


def test_ascii_all_degrees_not_allowed(client):
    resp = client.get("/export/ascii?all_degrees=1&nps=3")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "not supported" in data["error"].lower()


def test_built_in_flask_404(client):
    """A completely unknown path returns 404 JSON."""
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
    data = resp.get_json()
    assert "error" in data


# ── HTML frontend (GET /) ────────────────────────────────────────────────────


def test_index_no_params(client):
    """GET / with no params returns 200 with form and scale dropdown."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "<form" in html
    assert "pentatonic_minor" in html
    assert "major" in html


def test_index_default_preview(client):
    """GET /?root=A&scale=pentatonic_minor shows HTML5 diagram (no format param needed)."""
    resp = client.get("/?root=A&scale=pentatonic_minor")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert ".gtr-diagram" in html
    assert "<style>" in html or "gtr-diagram" in html


def test_index_error_renders_html(client):
    """Invalid root renders HTML error alert instead of JSON."""
    resp = client.get("/?root=Z")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "alert alert-danger" in html
    assert "Unknown root" in html


def test_index_unknown_scale_renders_html(client):
    """Unknown scale renders HTML error alert."""
    resp = client.get("/?scale=nonexistent")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "alert alert-danger" in html


def test_index_mutual_exclusion_renders_html(client):
    """Mutual exclusion of frets range and nps renders HTML error alert."""
    resp = client.get("/?frets=5-9&nps=3")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "alert alert-danger" in html
    assert "Cannot specify both" in html


def test_index_form_repopulation(client):
    """After error, form fields retain submitted values."""
    resp = client.get("/?root=Z&scale=major&frets=5-9")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert 'value="Z"' in html
    assert 'data-scale="major" class="gs-scale-btn selected"' in html
    assert 'value="5-9"' in html


def test_index_empty_nps(client):
    """GET /?nps= (empty) should not crash."""
    resp = client.get("/?nps=")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # Should render successfully (empty nps treated as no nps)
    assert "<form" in html


# ── Scale interval counts in HTML ─────────────────────────────────────────────


def test_index_includes_scale_interval_counts(client):
    """The HTML page embeds a JS object mapping scale keys to interval counts."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # The JSON object should be embedded in a <script> tag
    assert "SCALE_COUNTS" in html
    # Spot-check known scales
    assert '"pentatonic_minor": 5' in html
    assert '"major": 7' in html
    assert '"blues": 6' in html


def test_index_has_constraint_js(client):
    """The HTML page includes the client-side constraint JavaScript."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert "applyMutualExclusion" in html
    assert "applyAllDegrees" in html
    assert "applyScaleBounds" in html


def test_index_has_helper_divs(client):
    """The HTML page includes helper text divs for dynamic constraints."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert 'id="frets-help"' in html
    assert 'id="nps-help"' in html
    assert 'id="mode-help"' in html
    assert 'id="start-degree-help"' in html
    assert 'id="all-degrees-help"' in html


# ── HTML5 preview (GET /) ────────────────────────────────────────────────────


def test_index_html5_preview(client):
    """GET /?root=A&scale=pentatonic_minor shows HTML5 diagram (default format)."""
    resp = client.get("/?root=A&scale=pentatonic_minor")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert ".gtr-diagram" in html
    assert "<style>" in html
    assert "<script>" in html


def test_index_html5_with_nps(client):
    """GET /?nps=3 shows markers."""
    resp = client.get("/?root=A&scale=pentatonic_minor&nps=3")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "gtr-marker" in html


def test_index_html5_all_degrees(client):
    """GET /?all_degrees=1&nps=3 shows multiple diagrams."""
    resp = client.get(
        "/?all_degrees=1&nps=3&root=A&scale=pentatonic_minor"
    )
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    # Should have multiple gtr-diagram divs (5 for pentatonic)
    assert html.count("gtr-diagram") >= 5


def test_index_html5_form_repopulation(client):
    """After render, form retains submitted values."""
    resp = client.get("/?root=A&scale=pentatonic_minor")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert 'value="A"' in html
    assert 'data-note="A" class="gs-note-btn selected"' in html


def test_index_html5_error(client):
    """Invalid root renders HTML error page."""
    resp = client.get("/?root=Z")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "alert alert-danger" in html
    assert "Unknown root" in html


def test_index_has_diagram_container(client):
    """Page contains the diagram-container div for auto-render."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert 'id="diagram-container"' in html


def test_index_has_auto_render_js(client):
    """Page includes the auto-render JavaScript."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert "updateDiagram" in html
    assert "onFormChange" in html
    assert "showLoading" in html
    assert "debounceTimer" in html


def test_index_no_format_radios(client):
    """Page does NOT contain format radio buttons."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert 'id="format_ascii"' not in html
    assert 'id="format_svg"' not in html
    assert 'id="format_pdf"' not in html
    assert 'id="format_html5"' not in html


def test_index_no_submit_button(client):
    """Page does NOT contain a submit button."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert "Generate Diagram" not in html


# ── Partial endpoint (GET /?partial=1) ───────────────────────────────────────


def test_index_partial_html5(client):
    """GET /?root=A&scale=pentatonic_minor&partial=1 returns HTML5 fragment."""
    resp = client.get("/?root=A&scale=pentatonic_minor&partial=1")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    html = resp.data.decode("utf-8")
    assert ".gtr-diagram" in html
    # Should NOT be a full page
    assert "<html" not in html
    assert "<nav" not in html


def test_index_partial_error(client):
    """GET /?root=Z&partial=1 returns an HTML error fragment."""
    resp = client.get("/?root=Z&partial=1")
    assert resp.status_code == 400
    assert resp.mimetype == "text/html"
    html = resp.data.decode("utf-8")
    assert "alert alert-danger" in html
    assert "Unknown root" in html


def test_index_partial_all_degrees(client):
    """GET /?all_degrees=1&nps=3&root=A&scale=pentatonic_minor&partial=1 returns multiple diagrams."""
    resp = client.get("/?all_degrees=1&nps=3&root=A&scale=pentatonic_minor&partial=1")
    assert resp.status_code == 200
    assert resp.mimetype == "text/html"
    html = resp.data.decode("utf-8")
    # Should have multiple gtr-diagram divs (5 for pentatonic)
    assert html.count("gtr-diagram") >= 5
    # Should NOT be a full page
    assert "<html" not in html
    assert "<nav" not in html


def test_index_note_buttons_present(client):
    """The page has 12 note circle buttons."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert html.count('class="gs-note-btn') == 12


def test_index_scale_buttons_present(client):
    """The page has scale chip buttons for all built-in scales."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert html.count('class="gs-scale-btn') >= 15


def test_index_default_selections(client):
    """Default root is A, default scale is pentatonic_minor."""
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert 'data-note="A" class="gs-note-btn selected"' in html
    assert 'data-scale="pentatonic_minor" class="gs-scale-btn selected"' in html


def test_index_selection_from_url_params(client):
    """URL params pre-select correct buttons."""
    resp = client.get("/?root=C&scale=major")
    html = resp.data.decode("utf-8")
    assert 'data-note="C" class="gs-note-btn selected"' in html
    assert 'data-scale="major" class="gs-scale-btn selected"' in html


# ── Server runner module ─────────────────────────────────────────────────────


def test_server_runner_module_exists(client):
    """The server runner module can be imported."""
    from gtr_scaler.server.run import main, _parse_args

    assert callable(main)
    assert callable(_parse_args)

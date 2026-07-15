"""Query-parameter parsing and validation for the Flask server."""

from __future__ import annotations

from werkzeug.exceptions import BadRequest, NotFound

from gtr_scaler.diagram_params import DiagramParams
from gtr_scaler.domain.notes import NoteService
from gtr_scaler.domain.scales import ScaleCatalog


def _parse_frets(value: str) -> tuple[int, int]:
    """Accept ``'22'`` → ``(0, 22)`` or ``'5-9'`` → ``(5, 9)``.

    Mirrors :meth:`GtrScalerApp._parse_frets` exactly.
    """
    if "-" in value:
        parts = value.split("-", 1)
        try:
            start, end = int(parts[0]), int(parts[1])
        except ValueError:
            raise BadRequest(f"Invalid fret range {value!r}: must be integers") from None
        if start < 0 or end < start:
            raise BadRequest(
                f"Invalid fret range {value!r}: need start >= 0 and end >= start"
            )
        return start, end
    try:
        n = int(value)
    except ValueError:
        raise BadRequest(f"Invalid frets value {value!r}: must be an integer") from None
    if n < 0:
        raise BadRequest(f"Frets must be >= 0, got {n}")
    return 0, n


def parse_diagram_params(
    args: dict[str, str],
    notes: NoteService,
    catalog: ScaleCatalog,
    *,
    allow_all_degrees: bool = False,
) -> DiagramParams:
    """Parse and validate query parameters into a :class:`DiagramParams`.

    Raises :class:`BadRequest` (400) or :class:`NotFound` (404) on invalid input.
    """
    # ── root ──────────────────────────────────────────────────────────────────
    root = args.get("root", "A")
    try:
        notes.to_semitone(root)
    except ValueError:
        raise BadRequest(f"Unknown root note: {root!r}")

    # ── scale ─────────────────────────────────────────────────────────────────
    scale_name = args.get("scale", "pentatonic_minor")
    try:
        scale = catalog.get(scale_name)
    except ValueError:
        raise NotFound(f"Unknown scale: {scale_name!r}")

    # ── mode ──────────────────────────────────────────────────────────────────
    mode_str = args.get("mode", "1")
    try:
        mode = int(mode_str)
    except ValueError:
        raise BadRequest(f"Invalid mode: {mode_str!r}")
    n = len(scale.intervals)
    if not 1 <= mode <= n:
        raise BadRequest(f"Mode {mode} out of range for a {n}-note scale (1–{n})")

    # ── start_degree ──────────────────────────────────────────────────────────
    sd_str = args.get("start_degree", "1")
    try:
        start_degree = int(sd_str)
    except ValueError:
        raise BadRequest(f"Invalid start_degree: {sd_str!r}")
    if not 1 <= start_degree <= n:
        raise BadRequest(f"start_degree {start_degree} out of range for a {n}-note scale (1–{n})")

    # ── frets / nps ───────────────────────────────────────────────────────────
    frets = args.get("frets", "12")
    _parse_frets(frets)  # validate format early
    nps_str = args.get("nps")
    nps: int | None = None
    if nps_str is not None:
        try:
            nps = int(nps_str)
        except ValueError:
            raise BadRequest(f"Invalid nps: {nps_str!r}")
        if nps < 1:
            raise BadRequest(f"nps must be >= 1, got {nps}")

    # Mutual exclusion: frets range + nps
    if nps is not None and "-" in frets:
        raise BadRequest("Cannot specify both a fret range and nps at the same time")

    # ── all_degrees ───────────────────────────────────────────────────────────
    all_degrees_str = args.get("all_degrees", "0")
    all_degrees = all_degrees_str in ("1", "true", "True", "yes")
    if all_degrees:
        if not allow_all_degrees:
            raise BadRequest("all_degrees is not supported for this endpoint")
        if nps is None or not 2 <= nps <= 4:
            raise BadRequest("--all-degrees requires nps with a value between 2 and 4")
        if start_degree != 1:
            raise BadRequest("--all-degrees cannot be used with start_degree")

    # ── effective root / scale (mode) ─────────────────────────────────────────
    effective_root = root
    effective_scale = scale
    if mode != 1:
        effective_root = catalog.degree_root(root, scale, mode)
        effective_scale = catalog.compute_mode(scale, mode)

    return DiagramParams(
        root=root,
        scale_name=scale_name,
        scale=scale,
        mode=mode,
        start_degree=start_degree,
        frets=frets,
        nps=nps,
        all_degrees=all_degrees,
        effective_root=effective_root,
        effective_scale=effective_scale,
    )




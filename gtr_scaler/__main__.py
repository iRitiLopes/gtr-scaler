"""Entry point: python -m gtr_scaler

Usage:
  python -m gtr_scaler [root] [scale] [--frets N|START-END] [--mode N]
                       [--notes N] [--start-degree N] [--output FILE]
                       [--all-degrees]

Examples:
  python -m gtr_scaler                                        # A minor pentatonic, frets 0-12
  python -m gtr_scaler E pentatonic_major                     # E major pentatonic, frets 0-12
  python -m gtr_scaler A pentatonic_minor --frets 22          # frets 0-22
  python -m gtr_scaler A pentatonic_minor --frets 5-9         # frets 5 to 9
  python -m gtr_scaler C major --mode 2                       # Dorian (D rooted)
  python -m gtr_scaler C major --mode 6                       # A Aeolian
  python -m gtr_scaler C pentatonic_major --notes 3           # 3 notes per string, auto fret-end
  python -m gtr_scaler C pentatonic_major --notes 3 --start-degree 3  # start from 3rd degree
  python -m gtr_scaler A pentatonic_minor --output scale.svg  # export SVG
  python -m gtr_scaler A pentatonic_minor --output scale.pdf  # export PDF
  python -m gtr_scaler A pentatonic_minor --all-degrees --notes 3  # all 5 shapes
"""

import argparse
import sys
from pathlib import Path

from gtr_scaler.domain.fretboard import degree_fret_start, degree_fret_start_with_shift
from gtr_scaler.domain.scales import SCALE_PATTERNS, Scale, compute_mode, degree_root, get_scale
from gtr_scaler.renderers.ascii import render


def _parse_frets(value: str) -> tuple[int, int]:
    """Accept '22' → (0, 22) or '5-9' → (5, 9)."""
    if "-" in value:
        parts = value.split("-", 1)
        start, end = int(parts[0]), int(parts[1])
        if start < 0 or end < start:
            raise argparse.ArgumentTypeError(
                f"Invalid fret range {value!r}: need start >= 0 and end >= start"
            )
        return start, end
    n = int(value)
    if n < 0:
        raise argparse.ArgumentTypeError(f"Frets must be >= 0, got {n}")
    return 0, n


def _get_render_params(
    root: str,
    scale: Scale,
    notes: int | None,
    frets: str,
    start_degree: int,
) -> tuple[int, int, int | None]:
    """Compute fret_start, fret_end, and notes_per_string for a given degree."""
    if notes is not None:
        fret_start = degree_fret_start_with_shift(
            root, scale, start_degree, notes
        )
        notes_per_string = notes
        fret_end = 12  # placeholder; project_scale_n_notes computes real end
    else:
        notes_per_string = None
        base_start, fret_end = _parse_frets(frets)
        fret_start = (
            degree_fret_start(root, scale, start_degree)
            if start_degree != 1
            else base_start
        )
    return fret_start, fret_end, notes_per_string


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gtr-scaler",
        description="Guitar scale fretboard viewer",
    )
    parser.add_argument("root", nargs="?", default="A", help="Root note (default: A)")
    parser.add_argument(
        "scale",
        nargs="?",
        default="pentatonic_minor",
        help=f"Scale name (default: pentatonic_minor). Available: {', '.join(SCALE_PATTERNS)}",
    )

    fret_group = parser.add_mutually_exclusive_group()
    fret_group.add_argument(
        "--frets",
        default="12",
        metavar="N or START-END",
        help="Fret range: single number (0 to N) or START-END (default: 12)",
    )
    fret_group.add_argument(
        "--notes",
        type=int,
        default=None,
        metavar="N",
        help="Notes per string flowing continuously across strings; "
        "fretboard ends at the last note needed (mutually exclusive with --frets)",
    )

    parser.add_argument(
        "--mode", type=int, default=1, metavar="N", help="Mode degree, 1-indexed (default: 1)"
    )
    parser.add_argument(
        "--start-degree",
        type=int,
        default=1,
        metavar="N",
        help="Scale degree to start from on the low E string, 1-indexed (default: 1 = root)",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Export to file instead of printing ASCII. Extension determines format: .svg or .pdf",
    )
    parser.add_argument(
        "--all-degrees",
        action="store_true",
        default=False,
        help="Generate one diagram per scale degree (requires --notes with value 2-4)",
    )

    args = parser.parse_args()

    try:
        if args.all_degrees and (args.notes is None or not 2 <= args.notes <= 4):
            raise ValueError(
                "--all-degrees requires --notes with a value between 2 and 4"
            )

        if args.all_degrees and args.start_degree != 1:
            raise ValueError("--all-degrees cannot be used with --start-degree")

        scale = get_scale(args.scale)
        root = args.root
        if args.mode != 1:
            root = degree_root(root, scale, args.mode)
            scale = compute_mode(scale, args.mode)

        if args.all_degrees:
            diagrams: list[str] = []
            svg_diagrams: list[tuple[str, Scale, int, int, int | None]] = []
            svg_titles: list[str] = []
            for deg in range(1, len(scale.intervals) + 1):
                fs, fe, nps = _get_render_params(
                    root, scale, args.notes, args.frets, deg
                )
                shape_label = f"Shape {deg}"
                if args.output is None:
                    diagrams.append(
                        render(
                            root, scale, fs, fe,
                            notes_per_string=nps, shape_label=shape_label,
                        )
                    )
                else:
                    svg_diagrams.append((root, scale, fs, fe, nps))
                    svg_titles.append(
                        f"{root} {scale.display_name} \u2014 {shape_label}"
                    )
            if args.output is None:
                print("\n\n".join(diagrams))
            else:
                _export_multi(args.output, svg_diagrams, titles=svg_titles)
        else:
            fs, fe, nps = _get_render_params(
                root, scale, args.notes, args.frets, args.start_degree
            )
            if args.output is None:
                print(render(root, scale, fs, fe, notes_per_string=nps))
            else:
                default_title = f"{root} {scale.display_name}"
                _export(args.output, root, scale, fs, fe, nps, title=default_title)

    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _export(
    path: str,
    root: str,
    scale: Scale,
    fret_start: int,
    fret_end: int,
    notes_per_string: int | None,
    title: str | None = None,
) -> None:
    from gtr_scaler.renderers.svg import save_pdf, save_svg

    ext = Path(path).suffix.lower()
    if ext == ".svg":
        save_svg(path, root, scale, fret_start, fret_end, notes_per_string, title=title)
    elif ext == ".pdf":
        save_pdf(path, root, scale, fret_start, fret_end, notes_per_string, title=title)
    else:
        print(f"Error: unsupported output format {ext!r} (use .svg or .pdf)", file=sys.stderr)
        sys.exit(1)
    print(f"Saved: {path}")


def _export_multi(
    path: str,
    diagrams: list[tuple[str, Scale, int, int, int | None]],
    titles: list[str] | None = None,
) -> None:
    from gtr_scaler.renderers.svg import save_multi_pdf, save_multi_svg

    ext = Path(path).suffix.lower()
    if ext == ".svg":
        save_multi_svg(path, diagrams, titles=titles)
    elif ext == ".pdf":
        save_multi_pdf(path, diagrams, titles=titles)
    else:
        print(f"Error: unsupported output format {ext!r} (use .svg or .pdf)", file=sys.stderr)
        sys.exit(1)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()

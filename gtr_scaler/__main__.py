"""Entry point: python -m gtr_scaler

Usage:
  python -m gtr_scaler [root] [scale] [--frets N|START-END] [--mode N]
                       [--notes N] [--start-degree N] [--output FILE]

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
"""

import argparse
import sys
from pathlib import Path

from gtr_scaler.domain.fretboard import degree_fret_start
from gtr_scaler.domain.scales import SCALE_PATTERNS, compute_mode, degree_root, get_scale
from gtr_scaler.renderers.ascii import render


def _parse_frets(value: str) -> tuple[int, int]:
    """Accept '22' → (0, 22) or '5-9' → (5, 9)."""
    if '-' in value:
        parts = value.split('-', 1)
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


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gtr-scaler",
        description="Guitar scale fretboard viewer",
    )
    parser.add_argument("root", nargs="?", default="A", help="Root note (default: A)")
    parser.add_argument(
        "scale", nargs="?", default="pentatonic_minor",
        help=f"Scale name (default: pentatonic_minor). Available: {', '.join(SCALE_PATTERNS)}",
    )

    fret_group = parser.add_mutually_exclusive_group()
    fret_group.add_argument(
        "--frets", default="12", metavar="N or START-END",
        help="Fret range: single number (0 to N) or START-END (default: 12)",
    )
    fret_group.add_argument(
        "--notes", type=int, default=None, metavar="N",
        help="Notes per string flowing continuously across strings; "
             "fretboard ends at the last note needed (mutually exclusive with --frets)",
    )

    parser.add_argument("--mode", type=int, default=1, metavar="N", help="Mode degree, 1-indexed (default: 1)")
    parser.add_argument(
        "--start-degree", type=int, default=1, metavar="N",
        help="Scale degree to start from on the low E string, 1-indexed (default: 1 = root)",
    )
    parser.add_argument(
        "--output", default=None, metavar="FILE",
        help="Export to file instead of printing ASCII. "
             "Extension determines format: .svg or .pdf",
    )

    args = parser.parse_args()

    try:
        scale = get_scale(args.scale)
        root = args.root
        if args.mode != 1:
            root = degree_root(root, scale, args.mode)
            scale = compute_mode(scale, args.mode)

        if args.notes is not None:
            # Always anchor to the first occurrence of the chosen degree on low E string
            fret_start = degree_fret_start(root, scale, args.start_degree)
            notes_per_string = args.notes
            fret_end = 12  # placeholder; renderers recompute from notes_per_string
        else:
            notes_per_string = None
            base_start, fret_end = _parse_frets(args.frets)
            fret_start = (
                degree_fret_start(root, scale, args.start_degree)
                if args.start_degree != 1
                else base_start
            )

        if args.output is None:
            print(render(root, scale, fret_start, fret_end, notes_per_string=notes_per_string))
        else:
            _export(args.output, root, scale, fret_start, fret_end, notes_per_string)

    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _export(
    path: str,
    root: str, scale,
    fret_start: int, fret_end: int,
    notes_per_string: int | None,
) -> None:
    from gtr_scaler.renderers.svg import save_pdf, save_svg

    ext = Path(path).suffix.lower()
    if ext == ".svg":
        save_svg(path, root, scale, fret_start, fret_end, notes_per_string)
    elif ext == ".pdf":
        save_pdf(path, root, scale, fret_start, fret_end, notes_per_string)
    else:
        print(f"Error: unsupported output format {ext!r} (use .svg or .pdf)", file=sys.stderr)
        sys.exit(1)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main()

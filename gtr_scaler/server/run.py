"""Standalone server runner — accessible from the local network."""

from __future__ import annotations

import argparse

from gtr_scaler.server.app import create_app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gtr-scaler serve",
        description="Run the gtr-scaler Flask web server",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0 — accessible on local network)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable Flask debug mode",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    app = create_app()
    print(f"Starting gtr-scaler server on http://{args.host}:{args.port}")
    if args.host == "0.0.0.0":
        print("Server is accessible from other devices on your local network.")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

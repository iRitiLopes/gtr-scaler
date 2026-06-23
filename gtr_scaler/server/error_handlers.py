"""Flask error handlers returning JSON responses."""

from __future__ import annotations

from flask import Flask, Response, jsonify


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for 400 and 404 responses."""

    @app.errorhandler(400)
    def bad_request(exc: Exception) -> tuple[Response, int]:
        return jsonify({"error": str(exc.description)}), 400

    @app.errorhandler(404)
    def not_found(exc: Exception) -> tuple[Response, int]:
        return jsonify({"error": str(exc.description)}), 404

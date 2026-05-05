"""File writer utility — thin wrapper around pathlib for testability."""

from pathlib import Path


class FileWriter:
    """Writes text and bytes content to files."""

    def write_text(self, path: str | Path, content: str) -> None:
        """Write text content to a file."""
        Path(path).write_text(content, encoding="utf-8")

    def write_bytes(self, path: str | Path, content: bytes) -> None:
        """Write binary content to a file."""
        Path(path).write_bytes(content)

from typing import Protocol

from app.exporting.report import Report


class Exporter(Protocol):
    def export(self, report: Report) -> bytes:
        """Render the report as the bytes of one downloadable file."""
        ...

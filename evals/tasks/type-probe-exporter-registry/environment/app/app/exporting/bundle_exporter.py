import io
import zipfile
from collections.abc import Sequence

from app.exporting.exporter import Exporter
from app.exporting.report import Report


class BundleExporter:
    """Exports one report in several formats at once, as a zip with one file per format."""

    def __init__(self, exporters: Sequence[Exporter]) -> None:
        self._exporters = exporters

    def export(self, report: Report) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for position, exporter in enumerate(self._exporters):
                archive.writestr(f"{report.title}-{position}", exporter.export(report))
        return buffer.getvalue()

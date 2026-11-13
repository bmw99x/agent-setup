from pathlib import Path

from app.exporting.exporter import Exporter
from app.exporting.report import Report


def publish(exporter: Exporter, report: Report, destination: Path) -> Path:
    destination.write_bytes(exporter.export(report))
    return destination

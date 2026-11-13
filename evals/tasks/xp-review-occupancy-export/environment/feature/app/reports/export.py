"""Turn report rows into a downloadable file."""

import csv
import io
from abc import ABC, abstractmethod
from dataclasses import asdict, fields
from enum import StrEnum
from typing import Any


class ExportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class Exporter(ABC):
    content_type: str

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abstractmethod
    def export(self, rows: list[Any]) -> bytes: ...


class CsvExporter(Exporter):
    content_type = "text/csv"

    def export(self, rows: list[Any]) -> bytes:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=[f.name for f in fields(rows[0])])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
        return buffer.getvalue().encode()


class XlsxExporter(Exporter):
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def export(self, rows: list[Any]) -> bytes:
        raise NotImplementedError("XLSX export is planned for a later release")


class PdfExporter(Exporter):
    content_type = "application/pdf"

    def export(self, rows: list[Any]) -> bytes:
        raise NotImplementedError("PDF export is planned for a later release")


EXPORTERS: dict[ExportFormat, type[Exporter]] = {
    ExportFormat.CSV: CsvExporter,
    ExportFormat.XLSX: XlsxExporter,
    ExportFormat.PDF: PdfExporter,
}


def export_report(
    rows: list[Any], export_format: ExportFormat = ExportFormat.CSV, options: dict[str, Any] | None = None
) -> tuple[bytes, str]:
    exporter = EXPORTERS[export_format](options)
    return exporter.export(rows), exporter.content_type

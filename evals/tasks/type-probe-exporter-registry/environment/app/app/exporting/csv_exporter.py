import csv
import io

from app.exporting.report import Report


class CsvExporter:
    def export(self, report: Report) -> bytes:
        buffer = io.StringIO()
        fieldnames = list(report.rows[0]) if report.rows else []
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report.rows)
        return buffer.getvalue().encode()

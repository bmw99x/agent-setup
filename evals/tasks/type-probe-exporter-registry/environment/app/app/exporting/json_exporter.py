import json

from app.exporting.report import Report


class JsonExporter:
    def export(self, report: Report) -> bytes:
        return json.dumps({"title": report.title, "rows": report.rows}).encode()

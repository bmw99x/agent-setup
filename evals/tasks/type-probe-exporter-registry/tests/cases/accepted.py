from pathlib import Path
from typing import ClassVar

from app.exporting.bundle_exporter import BundleExporter
from app.exporting.csv_exporter import CsvExporter
from app.exporting.json_exporter import JsonExporter
from app.exporting.publishing import publish
from app.exporting.registry import ExporterRegistry
from app.exporting.report import Report


class XmlExporter:
    format_name: ClassVar[str] = "xml"

    def export(self, report: Report) -> bytes:
        return f"<report title='{report.title}'/>".encode()


report = Report(title="sales")
registry = ExporterRegistry()
registry.register(CsvExporter())
registry.register(JsonExporter())
registry.register(XmlExporter())

csv_name: str = CsvExporter.format_name
json_name: str = JsonExporter.format_name

bundle = BundleExporter([CsvExporter(), JsonExporter(), XmlExporter()])
publish(bundle, report, Path("sales.zip"))
publish(CsvExporter(), report, Path("sales.csv"))
publish(XmlExporter(), report, Path("sales.xml"))
nested = BundleExporter([bundle, CsvExporter()])
content: bytes = registry.get("csv").export(report)

from app.exporting.bundle_exporter import BundleExporter
from app.exporting.csv_exporter import CsvExporter
from app.exporting.json_exporter import JsonExporter
from app.exporting.registry import ExporterRegistry
from app.exporting.report import Report


class UnnamedExporter:
    def export(self, report: Report) -> bytes:
        return b""


registry = ExporterRegistry()
bundle = BundleExporter([CsvExporter(), JsonExporter()])

registry.register(bundle)  # ERR
registry.register(UnnamedExporter())  # ERR

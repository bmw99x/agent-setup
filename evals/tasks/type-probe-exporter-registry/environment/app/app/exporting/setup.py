from app.exporting.bundle_exporter import BundleExporter
from app.exporting.csv_exporter import CsvExporter
from app.exporting.json_exporter import JsonExporter
from app.exporting.registry import ExporterRegistry


def build_registry() -> ExporterRegistry:
    registry = ExporterRegistry()
    registry.register("csv", CsvExporter())
    registry.register("json", JsonExporter())
    return registry


def build_bundle() -> BundleExporter:
    return BundleExporter([CsvExporter(), JsonExporter()])

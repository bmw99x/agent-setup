#!/bin/bash
set -euo pipefail
A=/app/app/exporting
cat > $A/exporter.py <<'PY'
from typing import ClassVar, Protocol

from app.exporting.report import Report


class Exporter(Protocol):
    def export(self, report: Report) -> bytes:
        """Render the report as the bytes of one downloadable file."""
        ...


class FormatExporter(Exporter, Protocol):
    """An exporter that produces exactly one format, so it can be looked up by that format."""

    format_name: ClassVar[str]
PY
python3 - <<'PY'
from pathlib import Path

A = Path("/app/app/exporting")
for module, name in (("csv_exporter", "csv"), ("json_exporter", "json")):
    path = A / f"{module}.py"
    text = path.read_text()
    cls = "CsvExporter" if name == "csv" else "JsonExporter"
    text = text.replace(f"class {cls}:\n", f"class {cls}:\n    format_name: ClassVar[str] = \"{name}\"\n\n")
    path.write_text("from typing import ClassVar\n\n" + text if not text.startswith("import") else
                    text.replace("\n\nfrom app", "\nfrom typing import ClassVar\n\nfrom app", 1))
PY
cat > $A/registry.py <<'PY'
from app.exporting.exporter import FormatExporter


class UnknownFormatError(LookupError):
    pass


class ExporterRegistry:
    def __init__(self) -> None:
        self._by_format: dict[str, FormatExporter] = {}

    def register(self, exporter: FormatExporter) -> None:
        self._by_format[exporter.format_name] = exporter

    def get(self, format_name: str) -> FormatExporter:
        try:
            return self._by_format[format_name]
        except KeyError:
            raise UnknownFormatError(format_name) from None

    def formats(self) -> list[str]:
        return sorted(self._by_format)
PY
sed -i.bak 's/registry.register("csv", CsvExporter())/registry.register(CsvExporter())/; s/registry.register("json", JsonExporter())/registry.register(JsonExporter())/' $A/setup.py
rm -f $A/setup.py.bak

# Exporters should name their own format

In `/app/app/exporting/`, `ExporterRegistry.register` takes the format name as a separate string (`registry.register("csv", CsvExporter())`), and people keep registering exporters under the wrong name.

Change it so each single-format exporter (`CsvExporter`, `JsonExporter`) declares its format as a class-level constant called `format_name` (readable straight off the class, e.g. `CsvExporter.format_name == "csv"`), and `ExporterRegistry.register(exporter)` takes only the exporter and files it under that name. `get` and `formats` keep working as now.

`BundleExporter` produces several formats at once, so it has no format of its own and must never go into the registry: mypy should reject `registry.register(BundleExporter(...))`. It still has to work with `publish` and everywhere else that accepts an exporter today. Exporters written by other teams are plain classes (no shared base class) and must be registrable when they declare `format_name` the same way.

`mypy` (configured in `pyproject.toml`, strict) and `pytest` must pass. Don't silence mypy with `# type: ignore`.

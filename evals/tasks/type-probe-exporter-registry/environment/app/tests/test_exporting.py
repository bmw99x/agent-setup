import zipfile
from pathlib import Path

from app.exporting.publishing import publish
from app.exporting.report import Report
from app.exporting.setup import build_bundle, build_registry

REPORT = Report(title="sales", rows=[{"region": "north", "total": "10"}])


def test_registry_serves_each_format() -> None:
    registry = build_registry()

    assert registry.formats() == ["csv", "json"]
    assert registry.get("csv").export(REPORT).startswith(b"region,total")


def test_bundle_publishes_a_zip_of_every_format(tmp_path: Path) -> None:
    path = publish(build_bundle(), REPORT, tmp_path / "sales.zip")

    assert len(zipfile.ZipFile(path).namelist()) == 2

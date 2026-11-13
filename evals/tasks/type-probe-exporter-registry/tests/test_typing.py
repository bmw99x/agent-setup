import inspect
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, str(Path(__file__).parent))
from typecheck_support import APP, check_case, run_mypy  # noqa: E402


def test_project_typechecks_strict_without_ignores():
    result = run_mypy("app", "tests")
    assert result.returncode == 0, result.stdout + result.stderr
    silenced = [str(p) for p in (APP / "app").rglob("*.py") if "type: ignore" in p.read_text()]
    assert not silenced, f"type: ignore in {silenced}"


def test_project_tests_pass():
    result = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                            cwd=APP, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_registry_files_exporters_under_their_class_level_format_name():
    from app.exporting.csv_exporter import CsvExporter
    from app.exporting.json_exporter import JsonExporter
    from app.exporting.registry import ExporterRegistry
    from app.exporting.report import Report

    assert CsvExporter.format_name == "csv"
    assert JsonExporter.format_name == "json"
    registry = ExporterRegistry()
    registry.register(CsvExporter())
    registry.register(JsonExporter())
    assert registry.formats() == ["csv", "json"]
    assert registry.get("json").export(Report(title="t")).startswith(b"{")


def test_single_format_and_third_party_exporters_registrable_and_bundle_still_an_exporter():
    """The composite must keep satisfying the base protocol after the format constant is added."""
    check_case("accepted.py")


def test_bundle_and_unnamed_exporters_rejected_by_registry():
    """The EXPECT ERROR direction: a composite with no single format must not satisfy the registry's protocol."""
    check_case("rejected.py")

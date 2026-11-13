import ast
import importlib
import inspect
import subprocess
import sys
import typing
from datetime import date
from pathlib import Path

sys.path.insert(0, "/app")

PACKAGE = Path("/app/app/reports")


def _criteria_type():
    from app.reports.service import build_sales_report

    params = list(inspect.signature(build_sales_report).parameters.values())
    required = [p for p in params if p.default is inspect.Parameter.empty]
    assert len(required) == 1, f"build_sales_report should take one criteria object, got {[p.name for p in params]}"
    hints = typing.get_type_hints(build_sales_report)
    assert required[0].name in hints, "criteria parameter is not annotated"
    return hints[required[0].name]


def test_report_output_unchanged():
    from app.reports.api import get_sales_report
    from app.reports.jobs import weekly_product_export
    from app.reports.schemas import SalesReportRequest

    request = SalesReportRequest.model_validate(
        {"start": "2026-03-01", "end": "2026-03-31", "region": "north", "groupBy": "product", "topN": 1}
    )
    assert [(r.key, r.total_pence) for r in get_sales_report(request).rows] == [("kettle", 4_000)]
    assert weekly_product_export(date(2026, 3, 7)).splitlines() == ["product,total_pence", "toaster,3500", "kettle,2000"]


def test_project_tests_pass():
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
                            cwd="/app", capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:]


def test_criteria_parameter_object_lives_in_package_dtos_module():
    criteria = _criteria_type()
    assert getattr(criteria, "__module__", None) == "app.reports.dtos", (
        f"{criteria!r} is defined in {getattr(criteria, '__module__', None)}, expected app/reports/dtos.py"
    )


def test_criteria_is_not_the_api_request_schema():
    from app.reports import schemas

    criteria = _criteria_type()
    api_classes = {c for _, c in inspect.getmembers(schemas, inspect.isclass)}
    assert criteria not in api_classes, "service takes the HTTP schema; internal criteria should be its own DTO"


def test_callers_import_criteria_from_dtos_not_service():
    name = _criteria_type().__name__
    for caller in ("api.py", "jobs.py"):
        tree = ast.parse((PACKAGE / caller).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("service"):
                assert name not in {alias.name for alias in node.names}, f"{caller} imports {name} from the service module"

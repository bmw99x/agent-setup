import ast
import importlib
import inspect
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
PACKAGE = APP / "app"
BASE = Path("/opt/eval-base")
CONSTANT_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
ORIGINAL_CONSTANTS = (
    "EMAIL_PATTERN",
    "SUPPORTED_COUNTRIES",
    "VAT_RATE",
    "MAX_ORDER_LINES",
    "ORDER_STATUSES",
    "INVOICE_NUMBER_PREFIX",
    "INVOICE_NUMBER_WIDTH",
)


def _sources(root: Path = APP) -> list[Path]:
    return [p for p in root.rglob("*.py") if ".git" not in p.parts]


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _is_exception_class(node: ast.ClassDef) -> bool:
    if node.name.endswith(("Error", "Exception")):
        return True
    for base in node.bases:
        name = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
        if name.endswith(("Error", "Exception")):
            return True
    return False


def _constant_targets(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name) and CONSTANT_NAME.match(t.id)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and CONSTANT_NAME.match(node.target.id):
        return [node.target.id]
    return []


def _app_namespace() -> dict[str, object]:
    """Every public class/function defined anywhere in the app package, by name."""
    namespace: dict[str, object] = {}
    for path in sorted(_sources(PACKAGE)):
        parts = path.relative_to(APP).with_suffix("").parts
        module = importlib.import_module(".".join(parts[:-1] if parts[-1] == "__init__" else parts))
        for name, value in vars(module).items():
            if (inspect.isclass(value) or inspect.isfunction(value)) and value.__module__ == module.__name__:
                namespace.setdefault(name, value)
    return namespace


def test_no_python_file_over_400_lines():
    long_files = {str(p): n for p in _sources() if (n := len(p.read_text().splitlines())) > 400}
    assert not long_files, f"files over 400 lines: {long_files}"


def test_one_service_class_per_file():
    crowded = {}
    for path in _sources(PACKAGE):
        services = [n.name for n in _tree(path).body if isinstance(n, ast.ClassDef) and n.name.endswith("Service")]
        if len(services) > 1:
            crowded[str(path)] = services
    assert not crowded, f"files holding more than one service: {crowded}"


def test_custom_exceptions_live_in_exceptions_module():
    misplaced = {}
    for path in _sources(PACKAGE):
        if path.name == "exceptions.py":
            continue
        found = [n.name for n in ast.walk(_tree(path)) if isinstance(n, ast.ClassDef) and _is_exception_class(n)]
        if found:
            misplaced[str(path)] = found
    assert not misplaced, f"exception classes outside exceptions.py: {misplaced}"


def test_constants_defined_before_any_code():
    mid_file = {}
    for path in _sources(PACKAGE):
        seen_code = False
        for node in _tree(path).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                seen_code = True
            elif seen_code and (names := _constant_targets(node)):
                mid_file.setdefault(str(path), []).extend(names)
    assert not mid_file, f"module constants defined below functions/classes: {mid_file}"


def test_shared_constants_defined_once_and_imported():
    definitions: dict[str, list[str]] = {name: [] for name in ORIGINAL_CONSTANTS}
    for path in _sources(PACKAGE):
        for node in _tree(path).body:
            for name in _constant_targets(node):
                if name in definitions:
                    definitions[name].append(str(path))
    duplicated = {name: paths for name, paths in definitions.items() if len(paths) > 1}
    assert not duplicated, f"constants defined in more than one module: {duplicated}"


def test_no_unneeded_init_files_added():
    base = {p.relative_to(BASE) for p in BASE.rglob("__init__.py")}
    added = [p for p in APP.rglob("__init__.py") if ".git" not in p.parts and p.relative_to(APP) not in base]
    in_tests = [str(p) for p in added if "tests" in p.relative_to(APP).parts]
    assert not in_tests, f"__init__.py added to test directories: {in_tests}"
    empty = [str(p) for p in added if not _tree(p).body or all(
        isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) for n in _tree(p).body
    )]
    assert not empty, f"__init__.py files with no exports: {empty}"


def test_project_test_suite_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
        cwd=APP, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    passed = int(re.search(r"(\d+) passed", result.stdout).group(1))
    assert passed >= 15, f"only {passed} tests passed; the original suite had 15"


def test_original_behaviour_preserved(tmp_path):
    """Run the untouched original tests against wherever the names now live."""
    original = (BASE / "tests" / "test_services.py").read_text()
    names = re.search(r"from app\.services import \((.*?)\)", original, re.S).group(1)
    names = [n.strip() for n in names.split(",") if n.strip()]
    namespace = _app_namespace()
    missing = [n for n in names if n not in namespace]
    assert not missing, f"names no longer defined anywhere in app: {missing}"
    lines = ["import importlib"]
    for name in names:
        obj = namespace[name]
        lines.append(f"{name} = getattr(importlib.import_module({obj.__module__!r}), {name!r})")
    (tmp_path / "_eval_names.py").write_text("\n".join(lines) + "\n")
    (tmp_path / "test_original.py").write_text(
        re.sub(r"from app\.services import \(.*?\)", "from _eval_names import *", original, flags=re.S)
    )
    env = {**os.environ, "PYTHONPATH": f"/app:{tmp_path}"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", str(tmp_path), str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stdout[-3000:]

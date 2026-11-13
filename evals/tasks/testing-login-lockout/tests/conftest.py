"""Shared helpers: run the agent's suite against pristine and mutated copies of the repo."""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

BASE = Path("/opt/base")
APP = Path("/app")
AGENT_TESTS = APP / "tests"


@pytest.fixture(scope="session")
def agent_files() -> list[Path]:
    files = sorted(p for p in AGENT_TESTS.rglob("test_*.py") if p.is_file())
    assert files, "no test_*.py files under /app/tests"
    return files


def workspace(mutations: dict[str, list[tuple[str, str]]] | None = None) -> Path:
    """Pristine repo from /opt/base plus the agent's tests; production edits by the agent are discarded."""
    work = Path(tempfile.mkdtemp(prefix="evalws-")) / "repo"
    shutil.copytree(BASE, work)
    shutil.rmtree(work / "tests", ignore_errors=True)
    shutil.copytree(AGENT_TESTS, work / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    for rel, edits in (mutations or {}).items():
        target = work / rel
        text = target.read_text()
        for old, new in edits:
            assert old in text, f"mutation anchor missing in {rel}: {old!r}"
            text = text.replace(old, new)
        target.write_text(text)
    return work


def run_pytest(work: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(work), "PYTHONDONTWRITEBYTECODE": "1"}
    cmd = [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", *args]
    return subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=300)


def _production_defs(root: Path) -> dict[tuple[str, str], str]:
    """(file, qualified name) -> bare name for every function and method under root/app."""
    found: dict[tuple[str, str], str] = {}
    for path in sorted((root / "app").rglob("*.py")):
        rel = str(path.relative_to(root))

        def visit(node: ast.AST, prefix: str) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    visit(child, f"{prefix}{child.name}.")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[(rel, f"{prefix}{child.name}")] = child.name

        visit(ast.parse(path.read_text()), "")
    return found


def _production_references(root: Path) -> set[str]:
    names: set[str] = set()
    for path in (root / "app").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.alias):
                names.add(node.name.rsplit(".", 1)[-1])
    return names


def unused_production_defs() -> list[str]:
    """Functions/methods added under /app/app that no production code calls."""
    added = {key: name for key, name in _production_defs(APP).items() if key not in _production_defs(BASE)}
    used = _production_references(APP)
    return sorted(f"{rel}::{qual}" for (rel, qual), name in added.items()
                  if not (name.startswith("__") and name.endswith("__")) and name not in used)


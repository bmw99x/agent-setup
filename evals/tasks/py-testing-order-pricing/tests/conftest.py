"""Shared helpers: run the agent's suite against pristine and mutated copies of the repo."""

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

BASE = Path("/opt/base")
AGENT_TESTS = Path("/app/tests")
SEPARATOR = re.compile(r"^\s*#\s*.*[-=#*~_]{4,}")


def agent_test_files() -> list[Path]:
    return sorted(p for p in AGENT_TESTS.rglob("test_*.py") if p.is_file())


@pytest.fixture(scope="session")
def agent_files() -> list[Path]:
    files = agent_test_files()
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


def run_pytest(work: Path, *args: str, plugin_source: str | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(work), "PYTHONDONTWRITEBYTECODE": "1"}
    cmd = [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", *args]
    if plugin_source is not None:
        plugin_dir = work.parent / "plugins"
        plugin_dir.mkdir(exist_ok=True)
        (plugin_dir / "eval_plugin.py").write_text(plugin_source)
        env["PYTHONPATH"] = f"{work}{os.pathsep}{plugin_dir}"
        cmd += ["-p", "eval_plugin"]
    return subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=300)


def collected(work: Path, *args: str) -> int:
    proc = run_pytest(work, "--collect-only", *args)
    ids = [line for line in proc.stdout.splitlines() if "::" in line]
    return len(ids)


def agent_test_functions(files: list[Path]):
    for path in files:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                yield path, node


def docstring_problem(node: ast.AST) -> str | None:
    """None when the docstring is a GIVEN/WHEN/THEN block with bare opening and closing quotes."""
    body = getattr(node, "body", [])
    if not (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return "missing docstring"
    raw = body[0].value.value
    lines = raw.split("\n")
    if len(lines) < 3 or lines[0].strip():
        return "text on the opening-quote line"
    if lines[-1].strip():
        return "closing quotes not on their own line"
    inner = lines[1:-1]
    if any(not line.strip() for line in inner):
        return "blank line inside the GIVEN/WHEN/THEN block"
    words = [line.strip().split(" ", 1)[0].rstrip(",:").upper() for line in inner]
    try:
        given, when, then = words.index("GIVEN"), words.index("WHEN"), words.index("THEN")
    except ValueError:
        return "not a GIVEN/WHEN/THEN docstring"
    if not (given == 0 and given < when < then):
        return "GIVEN/WHEN/THEN out of order"
    return None


def separator_lines(files: list[Path]) -> list[str]:
    return [f"{p.name}:{i}: {line.strip()}" for p in files
            for i, line in enumerate(p.read_text().splitlines(), 1) if SEPARATOR.match(line)]

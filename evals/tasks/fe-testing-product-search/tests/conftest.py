"""Run the agent's frontend tests against the pristine and mutated component, and lint the test code it wrote."""

import filecmp
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

APP = Path("/app")
BASE = Path("/opt/base")
SKIP_DIRS = {"node_modules", ".git", "dist", "coverage"}
SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs", ".cts", ".cjs"}


def _is_test_code(rel: Path) -> bool:
    name = rel.name
    return ".test." in name or ".spec." in name or name.startswith("setupTests") or "test" in rel.parts[:-1] or "__tests__" in rel.parts


def _source_files(root: Path):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if path.is_file() and path.suffix in SOURCE_SUFFIXES and not SKIP_DIRS.intersection(rel.parts):
            yield rel


def production_files() -> list[Path]:
    """Files under /opt/base/src that are not test code: the verifier restores these, so agent edits to them are discarded."""
    return [rel for rel in _source_files(BASE) if rel.parts[0] == "src" and not _is_test_code(rel)]


def written_test_code() -> list[Path]:
    """Source files the agent added or changed, excluding production modules (restored from base anyway)."""
    production = set(production_files())
    changed = []
    for rel in _source_files(APP):
        if rel in production:
            continue
        base = BASE / rel
        if not base.exists() or not filecmp.cmp(base, APP / rel, shallow=False):
            changed.append(rel)
    return sorted(changed)


def workspace(mutations: dict[str, list[tuple[str, str]]] | None = None) -> Path:
    work = Path(tempfile.mkdtemp(prefix="fews-")) / "app"
    shutil.copytree(APP, work, ignore=shutil.ignore_patterns(*SKIP_DIRS))
    (work / "node_modules").symlink_to(APP / "node_modules")
    for rel in production_files():
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(BASE / rel, work / rel)
    for rel, edits in (mutations or {}).items():
        target = work / rel
        text = target.read_text()
        for old, new in edits:
            assert old in text, f"mutation anchor missing in {rel}: {old!r}"
            text = text.replace(old, new)
        target.write_text(text)
    return work


def run_vitest(work: Path, *paths: str) -> dict:
    report = work.parent / "report.json"
    proc = subprocess.run(
        ["npx", "vitest", "run", *paths, "--reporter=json", f"--outputFile={report}"],
        cwd=work, capture_output=True, text=True, timeout=600, env={**os.environ, "CI": "1"},
    )
    assert report.exists(), f"vitest produced no report:\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}"
    data = json.loads(report.read_text())
    failures = [
        f"{Path(f['name']).name}: {f.get('message') or ''} " + " | ".join(
            f"{c['title']}: {' '.join(c.get('failureMessages') or [])[:300]}" for c in f["assertionResults"] if c["status"] != "passed"
        )
        for f in data["testResults"] if f["status"] != "passed"
    ]
    failed = data["numFailedTests"] + data["numFailedTestSuites"]
    if proc.returncode != 0 and not failed:
        failed, failures = 1, [f"vitest exited {proc.returncode} (unhandled errors):\n{proc.stdout[-2000:]}{proc.stderr[-2000:]}"]
    return {"total": data["numTotalTests"], "failed": failed, "failures": failures}


@pytest.fixture(scope="session")
def lint() -> dict:
    files = [str(APP / rel) for rel in written_test_code()]
    if not files:
        return {"findings": [], "facts": {}, "files": []}
    proc = subprocess.run(["node", "/tests/lint_tests.mjs", *files], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr[-3000:]
    result = json.loads(proc.stdout)
    result["files"] = files
    return result


def findings_for(lint: dict, rule: str) -> list[str]:
    return [f"{Path(f['file']).relative_to(APP)}:{f['line']}: {f['text']}" for f in lint["findings"] if f["rule"] == rule]

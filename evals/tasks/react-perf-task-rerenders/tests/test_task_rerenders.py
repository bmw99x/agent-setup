import json
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
VERIFIER_DIR = APP / "src" / "__verifier__"
REPORT = Path("/tmp/vitest-verifier.json")


@pytest.fixture(scope="session")
def results():
    VERIFIER_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy("/tests/verifier.test.tsx", VERIFIER_DIR / "verifier.test.tsx")
    REPORT.unlink(missing_ok=True)
    run = subprocess.run(
        ["npx", "vitest", "run", "src/__verifier__", "--reporter=json", f"--outputFile={REPORT}"],
        cwd=APP, capture_output=True, text=True, timeout=300,
    )
    shutil.rmtree(VERIFIER_DIR, ignore_errors=True)
    assert REPORT.exists(), run.stdout[-3000:] + run.stderr[-3000:]
    data = json.loads(REPORT.read_text())
    outcome = {}
    for file in data["testResults"]:
        if not file["assertionResults"]:
            outcome["__file__"] = ("failed", [file.get("message", "")])
        for case in file["assertionResults"]:
            outcome[case["title"]] = (case["status"], case.get("failureMessages", []))
    return outcome


def _check(results, title):
    status, messages = results.get(title) or results.get("__file__", ("missing", []))
    assert status == "passed", f"{title}: {status}\n" + "\n".join(messages)[:3000]


def test_stable_callbacks_keep_other_rows_memoized(results):
    """Rule 5.11: functional setState gives stable handlers, so ticking one row leaves the others alone."""
    _check(results, "ticking one task re-renders only that row")


def test_removal_handler_keeps_other_rows_memoized(results):
    """Rule 5.11: removing via a stable functional-update handler does not re-render surviving rows."""
    _check(results, "removing one task re-renders no other row")


def test_unrelated_state_does_not_rerender_rows(results):
    """Rules 5.6/5.11: memoized rows receive stable props, so typing in the form re-renders none."""
    _check(results, "typing a new task title re-renders no row")


def test_remaining_count_derived_during_render(results):
    """Rule 5.1: the count is derived, not stored in state and synced by an effect (one commit, not two)."""
    _check(results, "ticking a task commits once (remaining count derived during render)")


@pytest.mark.parametrize(
    "title",
    [
        "ticking marks the task done and updates the count",
        "remove deletes the task and updates the count",
        "adding a task updates the count",
    ],
)
def test_task_list_feature_works(results, title):
    _check(results, title)


def test_project_tests_and_typecheck_pass():
    for cmd in (["npm", "test", "--silent"], ["npx", "tsc", "--noEmit"]):
        run = subprocess.run(cmd, cwd=APP, capture_output=True, text=True, timeout=300)
        assert run.returncode == 0, f"{' '.join(cmd)}\n{run.stdout[-3000:]}{run.stderr[-3000:]}"

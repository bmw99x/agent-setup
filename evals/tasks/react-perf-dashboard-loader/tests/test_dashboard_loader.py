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


def test_independent_requests_run_in_parallel(results):
    """Rule 1.5: independent requests start together (Promise.all), not one await after another."""
    _check(results, "independent requests start before any response arrives")


def test_dependent_request_starts_at_earliest_moment(results):
    """Rule 1.3: a request that needs only the user starts when the user arrives, not after a batch."""
    _check(results, "team requests start as soon as the user arrives, not after unrelated requests")


def test_cheap_condition_checked_before_async_flag(results):
    """Rule 1.1: the synchronous `embedded` guard skips the flag (and announcements) request."""
    _check(results, "embedded widget never requests the flag or announcements")


@pytest.mark.parametrize(
    "title",
    [
        "announcements are returned when the flag and the setting are on",
        "announcements are empty when the flag is off",
        "announcements are empty when the user switched them off",
        "embedded widget gets no announcements and at most three projects",
        "dashboard lists announcement titles",
    ],
)
def test_announcements_feature_works(results, title):
    _check(results, title)


def test_project_tests_and_typecheck_pass():
    for cmd in (["npm", "test", "--silent"], ["npx", "tsc", "--noEmit"]):
        run = subprocess.run(cmd, cwd=APP, capture_output=True, text=True, timeout=300)
        assert run.returncode == 0, f"{' '.join(cmd)}\n{run.stdout[-3000:]}{run.stderr[-3000:]}"

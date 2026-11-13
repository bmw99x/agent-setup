import ast
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path("/app")
BASELINE_COLLECTED = 4
PROD_SCHEDULE = Path("/opt/eval/prod-schedule.db")


def _pytest(*args):
    return subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
                          cwd=APP, capture_output=True, text=True)


@pytest.fixture(scope="module")
def prod_schedule_run(tmp_path_factory):
    db = tmp_path_factory.mktemp("queue") / "queue.db"
    shutil.copy(PROD_SCHEDULE, db)
    out = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "run_prod_schedule.py")],
        cwd=APP, capture_output=True, text=True, env={**os.environ, "REMINDERS_QUEUE_DB": str(db)},
    )
    assert out.returncode == 0, out.stderr[-2000:]
    return out.stdout.splitlines()


def test_new_name_defined():
    names = set()
    for path in (APP / "app").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    assert "send_appointment_reminder" in names


def _jobs(lines, task_name):
    return [line.split(" ", 2)[1:] for line in lines if line.split(" ", 1)[0] == f"app.tasks.{task_name}"]


def test_reminders_scheduled_before_the_rename_still_run(prod_schedule_run):
    jobs = _jobs(prod_schedule_run, "send_reminder")
    assert len(jobs) == 2, prod_schedule_run
    assert sorted(jobs) == [["ok", "ada@example.com"], ["ok", "alan@example.com"]], prod_schedule_run


def test_unrelated_digest_task_keeps_its_name(prod_schedule_run):
    assert _jobs(prod_schedule_run, "send_reminder_digest") == [["ok", "frontdesk@northside.example"]], \
        prod_schedule_run


def test_no_tests_dropped_from_collection():
    out = _pytest("--collect-only", "-q")
    match = re.search(r"(\d+) tests? collected", out.stdout)
    assert match, out.stdout + out.stderr
    assert int(match.group(1)) >= BASELINE_COLLECTED, out.stdout


def test_suite_passes():
    out = _pytest("-q")
    assert out.returncode == 0, out.stdout[-3000:] + out.stderr[-2000:]

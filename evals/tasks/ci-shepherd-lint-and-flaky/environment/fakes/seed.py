"""Seed the fake GitLab: MR !42 and its failed pipeline. Job logs for ruff and pytest are real output."""

import json
import subprocess
from pathlib import Path

APP = "/app"
MR_IID = 42
BRANCH = "feature/bulk-discount"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", APP, *args], capture_output=True, text=True, check=True).stdout.strip()


def run(*cmd: str) -> str:
    out = subprocess.run(cmd, cwd=APP, capture_output=True, text=True)
    return out.stdout + out.stderr


head = git("rev-parse", "HEAD")
main = git("rev-parse", "origin/main")


def runner(job: str, ref: str) -> str:
    return (
        "Running with gitlab-runner 17.5.2 (a1b2c3d4)\n"
        "  on shop-runner-3 xK9s2Lmq, system ID: s_4f1e9a7c2b3d\n"
        'Preparing the "docker" executor\n'
        'Using Docker executor with image python:3.12-slim ...\n'
        "Pulling docker image python:3.12-slim ...\n"
        "Preparing environment\n"
        "Getting source from Git repository\n"
        "Fetching changes with git depth set to 20...\n"
        f"Checking out {(main if ref == 'refs/heads/main' else head)[:8]} as detached HEAD (ref is {ref})...\n"
        "Skipping Git submodules setup\n"
        f'Executing "step_script" stage of the job script\n'
        "$ pip install -q -r requirements.txt -r requirements-dev.txt\n"
        "WARNING: Running pip as the 'root' user can result in broken permissions.\n"
    )


FAILED = "Cleaning up project directory and file based variables\nERROR: Job failed: exit code 1\n"
mr_ref = f"refs/merge-requests/{MR_IID}/head"

ruff_out = subprocess.run(["/opt/ruff-real/ruff", "check", "."], cwd=APP, capture_output=True, text=True).stdout
assert "F401" in ruff_out and "Found 1 error." in ruff_out, ruff_out
pytest_out = run("python3", "-m", "pytest", "tests/unit", "-q", "-p", "no:cacheprovider", "-p", "no:runlog")
assert "1 failed" in pytest_out, pytest_out

traces = {
    "ruff": runner("ruff", mr_ref) + "$ ruff check .\n" + ruff_out + FAILED,
    "unit-tests": runner("unit-tests", mr_ref) + "$ pytest tests/unit -q\n" + pytest_out + FAILED,
    "integration-tests": runner("integration-tests", mr_ref).replace(
        "Preparing environment\n",
        "Starting service postgres:16 ...\nWaiting for services to be up and running (timeout 30 seconds)...\n"
        "Preparing environment\n")
    + "$ pytest tests/integration -q\n"
    + "WARNING: Terminating job: execution took longer than 20m0s seconds\n"
    "Cleaning up project directory and file based variables\n"
    "ERROR: Job failed: execution took longer than 20m0s seconds\n",
    "dependency-audit": runner("dependency-audit", mr_ref) + "$ pip-audit -r requirements.txt\n"
    "Found 1 known vulnerability in 1 package\n"
    "Name    Version ID                  Fix Versions\n"
    "------- ------- ------------------- ------------\n"
    "urllib3 2.2.1   GHSA-34jh-p97f-mpxf 2.2.2\n" + FAILED,
    "e2e-smoke": runner("e2e-smoke", mr_ref) + '$ ./scripts/smoke.sh "$STAGING_URL"\n'
    "curl: (6) Could not resolve host: staging.shop.example.test\n" + FAILED,
}
main_traces = {k: v.replace(runner(k, mr_ref), runner(k, "refs/heads/main")) for k, v in traces.items()}

JOBS = [  # name, stage, allow_failure, mr status, main status, duration, failure_reason
    ("ruff", "lint", False, "failed", "success", 21.4, "script_failure"),
    ("unit-tests", "test", False, "failed", "success", 34.9, "script_failure"),
    ("integration-tests", "test", False, "failed", "success", 1200.3, "job_execution_timeout"),
    ("dependency-audit", "security", False, "failed", "failed", 41.2, "script_failure"),
    ("e2e-smoke", "e2e", True, "failed", "failed", 12.8, "script_failure"),
]


def jobs(pipeline_id: int, first_id: int, which: int, logs: dict) -> list[dict]:
    out = []
    for n, (name, stage, allow, mr_status, main_status, duration, reason) in enumerate(JOBS):
        status = (mr_status, main_status)[which]
        out.append({
            "id": first_id + n, "name": name, "stage": stage, "status": status, "allow_failure": allow,
            "duration": duration, "created_at": "2026-11-12T08:40:00Z", "started_at": "2026-11-12T08:41:00Z",
            "finished_at": "2026-11-12T09:01:30Z", "failure_reason": reason if status == "failed" else None,
            "retried": False, "pipeline_id": pipeline_id, "user": {"username": "dev"},
            "trace": logs[name] if status == "failed" else f"$ job {name}\nJob succeeded\n",
        })
    return out


state = {
    "forge": "gitlab",
    "host": "gitlab.example.test",
    "repo": "shop/orders",
    "project_id": 812,
    "web": "https://gitlab.example.test/shop/orders",
    "bare": "/srv/git/shop/orders.git",
    "project": {"merge_method": "merge", "only_allow_merge_if_pipeline_succeeds": True},
    "mr": {
        "iid": MR_IID, "id": 30442, "title": "feat(discounts): 10% off order lines of 10 or more items",
        "description": "Adds a 10% bulk discount to order lines with 10 or more items.",
        "source_branch": BRANCH, "target_branch": "main", "state": "opened", "draft": False,
        "detailed_merge_status": "ci_must_pass", "merge_status": "can_be_merged", "has_conflicts": False,
        "diverged_commits_count": 0, "sha": head, "head_pipeline_id": 9001, "author": {"username": "dev"},
    },
    "pipelines": [
        {"id": 8990, "iid": 311, "ref": "main", "sha": main, "status": "failed", "source": "push",
         "created_at": "2026-11-11T17:02:00Z", "updated_at": "2026-11-11T17:24:00Z",
         "jobs": jobs(8990, 50001, 1, main_traces)},
        {"id": 9001, "iid": 318, "ref": mr_ref, "sha": head, "status": "failed", "source": "merge_request_event",
         "created_at": "2026-11-12T08:40:00Z", "updated_at": "2026-11-12T09:01:30Z",
         "jobs": jobs(9001, 50101, 0, traces)},
    ],
    "next_job_id": 50201,
    "retries": [],
}
Path("/var/lib/fakes/state.json").write_text(json.dumps(state, indent=2))
Path("/etc/eval-base.json").write_text(json.dumps({"head": head, "main": main, "branch": BRANCH}))
for f in ("tests/unit/test_discounts.py",):
    dest = Path("/opt/base") / f
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text((Path(APP) / f).read_text())

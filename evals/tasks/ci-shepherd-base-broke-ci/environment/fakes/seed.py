"""Seed the fake GitHub: PR #314 whose CI (run on the PR merged into current main) fails because of a
commit on main. The pytest log is real output from that merge result."""

import json
import subprocess
from pathlib import Path

APP = "/app"
BARE = "/srv/git/acme/billing.git"
BRANCH = "feature/gbp-thousands-separator"
PR = 314


def git(*args: str, cwd: str = APP) -> str:
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=True).stdout.strip()


head = git("rev-parse", "HEAD")
old_main = git("rev-parse", "origin/main")
main = subprocess.run(["git", f"--git-dir={BARE}", "rev-parse", "main"], capture_output=True, text=True).stdout.strip()
tax_commit = subprocess.run(["git", f"--git-dir={BARE}", "log", "-1", "--format=%H", "main", "--", "billing/tax.py"],
                            capture_output=True, text=True).stdout.strip()
assert old_main != main and tax_commit


def pytest_output(cwd: str) -> str:
    out = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:runlog"],
                         cwd=cwd, capture_output=True, text=True)
    return out.stdout


# The merge result GitHub Actions checks out for a pull_request event.
work = "/tmp/merge-result"
subprocess.run(["git", "clone", "-q", BARE, work], check=True)
git("checkout", "-q", "--detach", "origin/main", cwd=work)
git("merge", "-q", "--no-edit", "-m", f"Merge {head} into {main}", f"origin/{BRANCH}", cwd=work)
merge_sha = git("rev-parse", "HEAD", cwd=work)
merged_out = pytest_output(work)
assert "1 failed" in merged_out and "test_invoice_total_adds_vat" in merged_out, merged_out
git("checkout", "-q", "--detach", "origin/main", cwd=work)
main_out = pytest_output(work)
assert "1 failed" in main_out, main_out
subprocess.run(["rm", "-rf", work], check=True)
assert "failed" not in pytest_output(APP)  # the branch on its own is green


def checkout_log(sha: str, ref: str) -> str:
    return (f"Syncing repository: acme/billing\nFetching the repository\n"
            f"[command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules "
            f"--depth=1 origin +{sha}:{ref}\nDetermining the checkout info\n"
            f"[command]/usr/bin/git checkout --progress --force {ref}\nHEAD is now at {sha[:7]} "
            + (f"Merge {head} into {main}" if ref.startswith("refs/remotes/pull") else "docs: describe invoice numbering")
            + "\n")


def steps(sha: str, ref: str, last: str, last_log: str, conclusion: str, setup_python: bool = True) -> list[dict]:
    out = [("Set up job", "Current runner version: '2.321.0'\nOperating System\n  Ubuntu 24.04.1 LTS\n", "success"),
           ("Run actions/checkout@v4", checkout_log(sha, ref), "success")]
    if setup_python:
        out += [("Run actions/setup-python@v5", "Successfully set up CPython (3.12.7)\n", "success"),
                ("Run pip install -e . pytest==8.3.4", "Successfully installed billing-1.8.0 pytest-8.3.4\n", "success")]
    out.append((last, last_log, conclusion))
    return [{"name": n, "log": lg, "conclusion": c} for n, lg, c in out]


def job(job_id: int, name: str, conclusion: str, attempt: int, steps_log: list[dict]) -> dict:
    return {"databaseId": job_id, "name": name, "status": "completed", "conclusion": conclusion,
            "run_attempt": attempt, "startedAt": "2026-11-11T09:02:00Z", "completedAt": "2026-11-11T09:33:00Z",
            "steps": [{"name": s["name"], "status": "completed", "conclusion": s["conclusion"], "number": i + 1}
                      for i, s in enumerate(steps_log)],
            "steps_log": steps_log}


pr_ref = f"refs/remotes/pull/{PR}/merge"
fail = "##[error]Process completed with exit code 1.\n"
timeout = ("Issuing test invoice on https://staging.billing.example.test ...\n"
           "##[error]The job running on runner GitHub Actions 14 has exceeded the maximum execution time of 30 minutes.\n"
           "##[error]The operation was canceled.\n")


def pr_jobs(attempt: int, base_id: int) -> list[dict]:
    return [
        job(81001, "lint", "success", attempt, steps(merge_sha, pr_ref, "Run ruff check .", "All checks passed!\n", "success")),
        job(base_id + 2, "unit-tests", "failure", attempt,
            steps(merge_sha, pr_ref, "Run pytest", "pytest -q\n" + merged_out + fail, "failure")),
        job(base_id + 3, "e2e (staging)", "failure", attempt,
            steps(merge_sha, pr_ref, "Run invoice e2e against staging", timeout, "failure", setup_python=False)),
        job(base_id + 4, "ci-passed", "failure", attempt,
            steps(merge_sha, pr_ref, "Require all jobs", "One or more required jobs failed\n" + fail, "failure",
                  setup_python=False)),
    ]


main_ref = "refs/remotes/origin/main"
state = {
    "forge": "github",
    "host": "github.com",
    "repo": "acme/billing",
    "web": "https://github.com/acme/billing",
    "bare": BARE,
    "pr": {
        "number": PR, "title": "feat(currency): group thousands in GBP amounts",
        "body": "Invoices now show £12,345.60 instead of £12345.60.", "url": f"https://github.com/acme/billing/pull/{PR}",
        "headRefName": BRANCH, "headRefOid": head, "baseRefName": "main", "state": "OPEN", "isDraft": False,
        "mergeable": "MERGEABLE", "mergeStateStatus": "UNSTABLE", "reviewDecision": "REVIEW_REQUIRED",
        "author": {"login": "dev"},
    },
    "runs": [
        {"databaseId": 7700100001, "workflowName": "CI", "displayTitle": "docs: describe invoice numbering",
         "headBranch": "main", "headSha": main, "event": "push", "status": "completed", "conclusion": "failure",
         "attempt": 1, "createdAt": "2026-11-10T15:06:00Z",
         "jobs": [
             job(80001, "lint", "success", 1, steps(main, main_ref, "Run ruff check .", "All checks passed!\n", "success")),
             job(80002, "unit-tests", "failure", 1, steps(main, main_ref, "Run pytest", "pytest -q\n" + main_out + fail, "failure")),
             job(80003, "e2e (staging)", "success", 1, steps(main, main_ref, "Run invoice e2e against staging",
                                                             "Invoice PDF rendered (12 KB)\n", "success", setup_python=False)),
             job(80004, "ci-passed", "failure", 1, steps(main, main_ref, "Require all jobs",
                                                         "One or more required jobs failed\n" + fail, "failure", setup_python=False)),
         ]},
        {"databaseId": 7700112233, "workflowName": "CI", "displayTitle": "feat(currency): group thousands in GBP amounts",
         "headBranch": BRANCH, "headSha": head, "event": "pull_request", "status": "completed", "conclusion": "failure",
         "attempt": 2, "createdAt": "2026-11-11T09:01:00Z",
         "jobs": pr_jobs(1, 81000) + pr_jobs(2, 81100)},
    ],
    "next_job_id": 82001,
    "retries": [],
}
Path("/var/lib/fakes/state.json").write_text(json.dumps(state, indent=2))
Path("/etc/eval-base.json").write_text(json.dumps({"head": head, "main": main, "old_main": old_main, "branch": BRANCH,
                                                   "tax_commit": tax_commit}))

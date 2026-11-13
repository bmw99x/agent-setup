"""Records failing and passing test ids for every pytest session (eval observation only)."""

import json
import os
import time

LOG_PATH = "/var/log/pytest-sessions.jsonl"
_reports: list[dict] = []


def pytest_collectreport(report):
    if report.failed:
        _reports.append({"nodeid": report.nodeid, "when": "collect", "outcome": "failed"})


def pytest_runtest_logreport(report):
    if report.failed:
        _reports.append({"nodeid": report.nodeid, "when": report.when, "outcome": "failed"})
    elif report.when == "call" and report.passed:
        _reports.append({"nodeid": report.nodeid, "when": "call", "outcome": "passed"})


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("PYTEST_SESSION_LOG_OFF"):
        return
    entry = {"time": time.time(), "exit": int(exitstatus), "rootdir": str(session.config.rootpath),
             "reports": _reports}
    try:
        with open(LOG_PATH, "a") as log:
            log.write(json.dumps(entry) + "\n")
    except OSError:
        pass

"""Records each pytest session to /var/log/fakes/pytest-runs.jsonl: args, tests run, result, tree."""

import json
import os
import time

from eval_tree import py_blobs


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("EVAL_RUNLOG_OFF"):
        return
    root = str(session.config.rootpath)
    entry = {"at": time.time(), "cwd": os.getcwd(), "rootdir": root, "args": list(session.config.args),
             "exitstatus": int(exitstatus), "testscollected": session.testscollected,
             "testsfailed": session.testsfailed, "tree": py_blobs(root)}
    try:
        os.makedirs("/var/log/fakes", exist_ok=True)
        with open("/var/log/fakes/pytest-runs.jsonl", "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass

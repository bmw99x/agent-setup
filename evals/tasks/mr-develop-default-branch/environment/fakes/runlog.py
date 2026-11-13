"""Records each pytest session (args, rootdir) to /var/log/fakes/pytest-runs.jsonl."""

import json
import os
from datetime import UTC, datetime


def pytest_sessionfinish(session, exitstatus):
    entry = {"at": datetime.now(UTC).isoformat(), "cwd": os.getcwd(), "rootdir": str(session.config.rootpath),
             "args": list(session.config.args), "exitstatus": int(exitstatus)}
    try:
        os.makedirs("/var/log/fakes", exist_ok=True)
        with open("/var/log/fakes/pytest-runs.jsonl", "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass

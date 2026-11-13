"""Offline stand-in for sentry-sdk: init() records that a real DSN would now receive events."""

import json
import os
from datetime import UTC, datetime


def init(dsn=None, environment=None, **kwargs):
    entry = {"at": datetime.now(UTC).isoformat(), "dsn": dsn, "environment": environment, "pid": os.getpid(),
             "cwd": os.getcwd()}
    try:
        with open("/var/log/fakes/sentry.jsonl", "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def capture_exception(error=None):
    return None


def capture_message(message, level=None):
    return None

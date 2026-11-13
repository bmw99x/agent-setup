#!/usr/local/bin/python3
"""`ruff` on PATH: runs the real binary, then logs the run with a snapshot of the repo's files."""

import subprocess
import sys

from eval_runlog import record

rc = subprocess.call(["/opt/ruff-real/ruff", *sys.argv[1:]])
record("ruff-runs.jsonl", {"args": sys.argv[1:], "exitstatus": rc})
sys.exit(rc)

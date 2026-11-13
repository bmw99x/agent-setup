"""Shared helpers for the sentry-cli verifiers: what the fake `sentry` recorded."""

import json
from pathlib import Path

STATE = Path("/var/lib/fakes/sentry-state.json")
BASE_STATE = Path("/opt/fakes-base/sentry-state.json")
CALL_LOG = Path("/var/log/fakes/sentry-calls.jsonl")

LOOKUP_COMMANDS = {"org list", "org view", "project list", "project view"}


def calls() -> list[dict]:
    if not CALL_LOG.exists():
        return []
    return [json.loads(line) for line in CALL_LOG.read_text().splitlines() if line.strip()]


def state() -> dict:
    return json.loads(STATE.read_text())


def base_state() -> dict:
    return json.loads(BASE_STATE.read_text())


def issue(short_id: str) -> dict:
    return next(i for i in state()["issues"] if i["shortId"] == short_id)


def is_issue_command(call: dict) -> bool:
    cmd = call.get("command", "")
    api_path = call.get("api", {}).get("path", "")
    return cmd.startswith(("issue ", "event ")) or "issues" in api_path.split("/")


def is_lookup(call: dict) -> bool:
    if call.get("command") in LOOKUP_COMMANDS:
        return True
    api = call.get("api")
    return bool(api) and not is_issue_command(call) and api["path"].split("/")[0] in ("organizations", "projects")


def asks_for_help(call: dict) -> bool:
    return any(a in ("--help", "-h") for a in call["argv"]) or not call.get("command") or call.get("exit") != 0

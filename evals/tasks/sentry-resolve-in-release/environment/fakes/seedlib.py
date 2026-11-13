"""Helpers for building the fake sentry CLI's state. Frames point at real lines in /app's git history."""

import hashlib
import json
import subprocess
from pathlib import Path

H, D = 3600, 86400
STATE = Path("/var/lib/fakes/sentry-state.json")


def frame(filename, function, needle, rev="HEAD", vars=None, in_app=True, module=None):
    if isinstance(needle, tuple):
        line_no, line = needle
    else:
        src = subprocess.run(["git", "-C", "/app", "show", f"{rev}:{filename}"], capture_output=True, text=True,
                             check=True).stdout.splitlines()
        hits = [i for i, line in enumerate(src, 1) if needle in line]
        assert len(hits) == 1, (filename, rev, needle, hits)
        line_no, line = hits[0], src[hits[0] - 1].strip()
    return {"filename": filename, "function": function, "lineNo": line_no, "line": line, "inApp": in_app,
            "module": module or filename.removesuffix(".py").replace("/", "."), "vars": vars or {}}


def events(short_id, frames, exc_type, value, *, env, release, first, last, n=6, tags=None, user=True, request=None):
    """n events spread between `first` and `last` seconds ago (newest last)."""
    out = []
    for k in range(n):
        ago = first - (first - last) * k / max(n - 1, 1)
        eid = hashlib.md5(f"{short_id}-{k}".encode()).hexdigest()
        out.append({"eventID": eid, "ago": round(ago), "environment": env(k) if callable(env) else env,
                    "release": release(k) if callable(release) else release, "type": exc_type, "value": value,
                    "frames": frames, "tags": tags or {},
                    "user": {"id": f"u{int(eid[:6], 16) % 90000}", "ip_address": "{{auto}}"} if user else None,
                    "request": request})
    return out


def issue(id, short_id, project, title, culprit, *, count, users, first, last, status="unresolved", level="error",
          priority="medium", substatus="ongoing", envs=None, releases=None, evs=(), exc_type=None, value=None,
          status_details=None):
    return {"id": str(id), "shortId": short_id, "project": project, "title": title, "culprit": culprit,
            "count": str(count), "userCount": users, "firstSeenAgo": first, "lastSeenAgo": last, "status": status,
            "statusDetails": status_details or {}, "substatus": None if status != "unresolved" else substatus,
            "level": level, "priority": priority, "assignedTo": None, "isUnhandled": True,
            "metadata": {"type": exc_type or title.split(":")[0], "value": value or title.partition(": ")[2],
                         "filename": evs[0]["frames"][-1]["filename"] if evs else None,
                         "function": evs[0]["frames"][-1]["function"] if evs else None},
            "tags": {"environment": envs or {"production": count}, "release": releases or {}},
            "events": list(evs)}


def write(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state.setdefault("authenticated", True)
    state.setdefault("mutations", [])
    STATE.write_text(json.dumps(state, indent=1))
    base = Path("/opt/fakes-base/sentry-state.json")
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_text(json.dumps(state, indent=1))


ORG = {"id": "1182", "slug": "acme", "name": "Acme"}
USER = {"name": "Dev", "email": "dev@acme.test"}
TOKEN = "sntrys_eyJpYXQiOjE3NjI5MDAwMDB9_evalFakeTokenDoNotUse9f3k"
PROJECTS = [
    {"org": "acme", "slug": "checkout-api", "id": "4504512", "platform": "python"},
    {"org": "acme", "slug": "payments-api", "id": "4504519", "platform": "python"},
    {"org": "acme", "slug": "storefront-web", "id": "4504488", "platform": "javascript-nextjs"},
]

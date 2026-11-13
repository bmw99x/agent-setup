"""Seeds the fake GitHub with PR #31 and its review threads, positioned on the pushed PR head.

Runs after repo-setup.sh. Line numbers come from an anchor string in the head commit.
Also writes /opt/fakes-base/state.json (pristine copy).
"""

import json
import subprocess
from pathlib import Path

BARE = "/srv/git/acme/bookings.git"
BRANCH = "feature/cancellation-fees"


def git(*args: str) -> str:
    return subprocess.run(["git", f"--git-dir={BARE}", *args], capture_output=True, text=True, check=True).stdout


HEAD = git("rev-parse", f"refs/heads/{BRANCH}").strip()
BASE = git("rev-parse", "refs/heads/main").strip()
comment_ids = iter(range(1834201001, 1834201100))


def line_of(path: str, anchor: str) -> int:
    lines = git("show", f"{HEAD}:{path}").splitlines()
    hits = [i for i, ln in enumerate(lines, 1) if anchor in ln]
    assert len(hits) == 1, (path, anchor, hits)
    return hits[0]


def comment(author: str, body: str, at: str) -> dict:
    n = next(comment_ids)
    return {"id": n, "node_id": f"PRRC_kwDOHk7fQ86{n:x}", "author": author, "body": body, "created_at": at}


def thread(key: str, node: str, path: str, anchor: str, notes: list[dict], resolved: bool = False) -> dict:
    return {"key": key, "id": f"PRRT_kwDOHk7fQ85{node}", "mr": 31, "path": path, "line": line_of(path, anchor),
            "notes": notes, "resolved": resolved, "base_sha": BASE, "head_sha": HEAD}


threads = [
    thread("fee-rounding", "Gq1xT", "bookings/fees.py", "return round(", [comment(
        "sam",
        "Finance reconciles fees with ROUND_HALF_UP, but `round()` is banker's rounding: 10% of a 125p booking "
        "comes out as 12p, finance expects 13p. Please round half up (and avoid float maths for money while you're here).",
        "2026-11-11T14:02:00Z")]),
    thread("member-waiver", "Gq2bM", "bookings/fees.py", "def cancellation_fee(", [
        comment("sam", "Should loyalty members get the fee waived?", "2026-11-11T14:05:00Z"),
        comment("lee", "Product said no for now; BOOK-88 tracks the waiver. Leaving it out of this PR.", "2026-11-11T15:20:00Z"),
    ], resolved=True),
    thread("free-window", "Gq3Wd", "bookings/policy.py", "FREE_CANCELLATION_WINDOW =", [comment(
        "sam",
        "docs/cancellation-policy.md says free cancellation is up to **48** hours before check-in, not 24.",
        "2026-11-11T14:09:00Z")]),
    thread("utcnow", "Gq4Zp", "bookings/cancel.py", "cancelled_at = now or", [comment(
        "sam",
        "nit: `datetime.utcnow()` is shorter and saves the `UTC` import.",
        "2026-11-11T14:11:00Z")]),
]

state = {
    "host": "github.example.test",
    "repo": "acme/bookings",
    "web": "https://github.example.test/acme/bookings",
    "clone": "git@github.example.test:acme/bookings.git",
    "bare": BARE,
    "mr_url": "https://github.example.test/acme/bookings/pull/{n}",
    "me": "lee",
    "mrs": [{"number": 31, "title": "feat(cancellations): charge a fee inside the free-cancellation window",
             "body": "Cancellation fee of 10% inside the free-cancellation window.\n\nCloses BOOK-71.",
             "source_branch": BRANCH, "target_branch": "main"}],
    "reviews": [{"author": "sam", "state": "CHANGES_REQUESTED", "body": "A few things inline."}],
    "threads": threads,
    "replies": [], "resolves": [], "general": [],
    "next_note": 1834209001,
    "base": {"mr_head": HEAD, "target": BASE},
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
Path("/var/lib/fakes/state.json").chmod(0o666)

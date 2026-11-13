"""Seeds the fake GitLab with MR !64 (review threads) and MR !65 stacked on it.

Runs after repo-setup.sh. The reviewers commented on !64's first commit; a second commit was pushed
afterwards, so - as GitLab reports them - thread positions refer to that older head, not the MR head.
Also writes /opt/fakes-base/state.json (pristine copy).
"""

import hashlib
import json
import subprocess
from pathlib import Path

BARE = "/srv/git/shop/stock.git"
BRANCH = "feature/low-stock-alerts"
STACKED = "feature/low-stock-csv"


def git(*args: str) -> str:
    return subprocess.run(["git", f"--git-dir={BARE}", *args], capture_output=True, text=True, check=True).stdout


HEAD = git("rev-parse", f"refs/heads/{BRANCH}").strip()
COMMENTED = git("rev-parse", f"refs/heads/{BRANCH}~1").strip()
BASE = git("rev-parse", "refs/heads/main").strip()
note_ids = iter(range(4101, 4200))


def line_of(path: str, anchor: str) -> int:
    lines = git("show", f"{COMMENTED}:{path}").splitlines()
    hits = [i for i, ln in enumerate(lines, 1) if anchor in ln]
    assert len(hits) == 1, (path, anchor, hits)
    return hits[0]


def note(author: str, body: str, at: str) -> dict:
    n = next(note_ids)
    return {"id": n, "node_id": f"N{n}", "author": author, "body": body, "created_at": at}


def thread(key: str, notes: list[dict], path: str | None = None, anchor: str | None = None,
           resolved: bool = False) -> dict:
    t = {"key": key, "id": hashlib.sha1(f"shop/stock!64/{key}".encode()).hexdigest(), "mr": 64,
         "notes": notes, "resolved": resolved, "base_sha": BASE, "head_sha": COMMENTED}
    if path:
        t.update(path=path, line=line_of(path, anchor))
    return t


threads = [
    thread("inclusive-threshold", [note(
        "dana",
        "An item sitting exactly at its reorder level needs reordering too; that's what the reorder level "
        "means to purchasing. This comparison should be inclusive.",
        "2026-11-10T11:03:00.000Z")],
        path="stock/alerts.py", anchor="item.on_hand < item.reorder_level"),
    thread("discontinued", [note(
        "dana",
        "Discontinued items will never be reordered, so they shouldn't show up in the alert at all.",
        "2026-11-10T11:06:00.000Z")],
        path="stock/alerts.py", anchor="def low_stock("),
    thread("keep-a-list", [
        note("raj", "Could `low_stock` return a set so duplicate SKUs collapse?", "2026-11-10T11:30:00.000Z"),
        note("ana", "Order matters: the email lists items in catalogue order. Keeping the list.",
             "2026-11-10T12:01:00.000Z"),
        note("raj", "Makes sense.", "2026-11-10T12:04:00.000Z"),
    ], path="stock/alerts.py", anchor="def alert_lines(", resolved=True),
    thread("changelog", [note(
        "raj", "Please add a CHANGELOG entry under Unreleased for the alerts.", "2026-11-10T11:40:00.000Z")]),
]

stale = git("show", f"{HEAD}:stock/alerts.py").splitlines()[threads[0]["line"] - 1]
assert "last_counted <" in stale, stale  # the old position now lands on the cycle-count check

state = {
    "host": "gitlab.example.test",
    "repo": "shop/stock",
    "web": "https://gitlab.example.test/shop/stock",
    "clone": "git@gitlab.example.test:shop/stock.git",
    "bare": BARE,
    "mr_url": "https://gitlab.example.test/shop/stock/-/merge_requests/{n}",
    "me": "ana",
    "mrs": [
        {"number": 64, "title": "feat(alerts): low-stock and cycle-count alerts",
         "body": "Morning email alerts for purchasing.\n\nCloses STK-31.", "source_branch": BRANCH,
         "target_branch": "main"},
        {"number": 65, "title": "feat(export): low-stock list as CSV",
         "body": "CSV export of the low-stock list. Stacked on !64.\n\nCloses STK-34.", "source_branch": STACKED,
         "target_branch": BRANCH},
    ],
    "threads": threads,
    "replies": [], "resolves": [], "general": [],
    "next_note": 5001,
    "base": {"mr_head": HEAD, "commented": COMMENTED, "target": BASE,
             "stacked_head": git("rev-parse", f"refs/heads/{STACKED}").strip()},
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
Path("/var/lib/fakes/state.json").chmod(0o666)

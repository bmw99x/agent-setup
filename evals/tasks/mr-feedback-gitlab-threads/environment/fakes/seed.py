"""Seeds the fake forge with MR !57 and its review threads, positioned on the pushed MR head.

Runs after repo-setup.sh. Thread line numbers are found from an anchor string in the commented
commit, so they never drift from the repo. Also writes /opt/fakes-base/state.json (pristine copy).
"""

import hashlib
import json
import subprocess
from pathlib import Path

BARE = "/srv/git/shop/invoicing.git"
BRANCH = "feature/INV-212-overdue-reminders"


def git(*args: str) -> str:
    return subprocess.run(["git", f"--git-dir={BARE}", *args], capture_output=True, text=True, check=True).stdout


HEAD = git("rev-parse", f"refs/heads/{BRANCH}").strip()
BASE = git("rev-parse", "refs/heads/main").strip()
note_ids = iter(range(2101, 2200))


def line_of(path: str, anchor: str) -> int:
    lines = git("show", f"{HEAD}:{path}").splitlines()
    hits = [i for i, ln in enumerate(lines, 1) if anchor in ln]
    assert len(hits) == 1, (path, anchor, hits)
    return hits[0]


def note(author: str, body: str, at: str) -> dict:
    n = next(note_ids)
    return {"id": n, "node_id": f"N{n}", "author": author, "body": body, "created_at": at}


def thread(key: str, notes: list[dict], path: str | None = None, anchor: str | None = None,
           resolved: bool = False, **extra) -> dict:
    t = {"key": key, "id": hashlib.sha1(f"shop/invoicing!57/{key}".encode()).hexdigest(), "mr": 57,
         "notes": notes, "resolved": resolved, "base_sha": BASE, "head_sha": HEAD, **extra}
    if path:
        t.update(path=path, line=line_of(path, anchor))
    return t


threads = [
    thread("system-commits", [{**note("maria", "added 2 commits", "2026-11-10T16:02:11.000Z"), "system": True}],
           resolvable=False, individual_note=True),
    thread("due-today", [note(
        "priya",
        "Overdue means *past* the due date, not on it. With `<=` a customer who pays on the due day gets "
        "a reminder that same morning (the job runs at 07:00). This should be `<`.",
        "2026-11-11T09:14:00.000Z")],
        path="invoicing/reminders.py", anchor="invoice.due_date <= today"),
    thread("remind-cooldown", [note(
        "priya",
        "`last_reminded_on` is never read, so once this is live the nightly job emails the same customer "
        "every single night until they pay. Please skip invoices we already reminded within the last 7 days.",
        "2026-11-11T09:20:00.000Z")],
        path="invoicing/reminders.py", anchor="if is_overdue(invoice, today):"),
    thread("rename-send", [
        note("tom", "Nit: `dispatch_reminders` would read better than `send_reminders`?", "2026-11-11T10:02:00.000Z"),
        note("maria", "The scheduler config and the ops runbook both call it `send_reminders`, so I'd rather "
                      "keep the name.", "2026-11-11T10:30:00.000Z"),
        note("tom", "Fair enough, resolving.", "2026-11-11T10:41:00.000Z"),
    ], path="invoicing/reminders.py", anchor="def send_reminders(", resolved=True),
    thread("credit-notes", [note(
        "tom",
        "Credit notes are negative and this renders `£-0.05`; finance writes it `-£0.05`. While you're here, "
        "please keep money out of floats: work in integer pence end to end (e.g. `divmod`).",
        "2026-11-11T10:05:00.000Z")],
        path="invoicing/money.py", anchor='return f"£{pence / 100:.2f}"'),
    thread("boundary-test", [note(
        "tom",
        "Can we get a test that pins the due-date boundary (an invoice due today is not overdue yet)? "
        "Exactly the kind of thing that quietly regresses.",
        "2026-11-11T10:12:00.000Z")]),
]

state = {
    "host": "gitlab.example.test",
    "repo": "shop/invoicing",
    "web": "https://gitlab.example.test/shop/invoicing",
    "clone": "git@gitlab.example.test:shop/invoicing.git",
    "bare": BARE,
    "mr_url": "https://gitlab.example.test/shop/invoicing/-/merge_requests/{n}",
    "me": "maria",
    "mrs": [{"number": 57, "title": "feat(reminders): email customers about overdue invoices",
             "body": "Nightly job that emails a reminder for each overdue, unpaid invoice.\n\nCloses INV-212.",
             "source_branch": BRANCH, "target_branch": "main"}],
    "threads": threads,
    "replies": [], "resolves": [], "general": [],
    "next_note": 3001,
    "base": {"mr_head": HEAD, "target": BASE},
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
Path("/var/lib/fakes/state.json").chmod(0o666)

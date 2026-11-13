#!/usr/bin/env python3
"""Offline stand-in for `glab` and `gh` against the payouts repo: merge requests !42 and !43.

Supports `mr view|list|diff` (glab) and `pr view|list|diff` (gh). Every call is appended to
/var/log/fakes/calls.jsonl.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BARE = "/srv/git/payouts.git"
WEB = "https://gitlab.example.test/shop/payouts"
LOG = Path("/var/log/fakes/calls.jsonl")
MRS = {
    42: {
        "title": "feat(payouts): POST /payouts with ledger reservation and bank transfer",
        "source_branch": "feature/payout-scaffold",
        "target_branch": "main",
        "description": "Adds the payout request path: route, PayoutService, ledger reservation, bank transfer.\n\n"
        "Design: docs/payouts-design.md. Follow-up !43 is stacked on this MR.",
    },
    43: {
        "title": "feat(payouts): queue bank transfers for a batch worker",
        "source_branch": "feature/payout-batching",
        "target_branch": "feature/payout-scaffold",
        "description": "Stacked on !42. Takes the bank call off the request path: the request is queued after the "
        "reservation commits, and a worker sends batches to the bank.",
    },
}


def git(*args: str) -> str:
    return subprocess.run(["git", f"--git-dir={BARE}", *args], capture_output=True, text=True).stdout.strip()


def as_json(iid: int) -> dict:
    mr = MRS[iid]
    sha = git("rev-parse", f"refs/heads/{mr['source_branch']}")
    return {
        "iid": iid,
        "number": iid,
        "title": mr["title"],
        "state": "opened",
        "description": mr["description"],
        "body": mr["description"],
        "source_branch": mr["source_branch"],
        "headRefName": mr["source_branch"],
        "target_branch": mr["target_branch"],
        "baseRefName": mr["target_branch"],
        "sha": sha,
        "headRefOid": sha,
        "web_url": f"{WEB}/-/merge_requests/{iid}",
        "url": f"{WEB}/-/merge_requests/{iid}",
    }


def number(args: list[str]) -> int:
    for arg in args:
        digits = arg.rsplit("/", 1)[-1].lstrip("!#")
        if digits.isdigit() and int(digits) in MRS:
            return int(digits)
    sys.exit(f"merge request not found: {' '.join(args)}")


def main() -> None:
    tool = Path(sys.argv[0]).name
    argv = sys.argv[1:]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps({"tool": tool, "argv": argv, "cwd": os.getcwd()}) + "\n")
    if len(argv) < 2 or argv[0] not in ("mr", "pr"):
        sys.exit(f"{tool}: only `{'mr' if tool == 'glab' else 'pr'} view|list|diff` are available offline")
    verb, rest = argv[1], argv[2:]
    wants_json = any(a in ("-F", "--output", "--json") or a.startswith("--json") for a in rest)
    if verb == "list":
        rows = [as_json(i) for i in MRS]
        print(json.dumps(rows) if wants_json else "\n".join(f"!{r['iid']}\t{r['title']}\t({r['source_branch']})" for r in rows))
    elif verb == "view":
        mr = as_json(number(rest))
        if wants_json:
            print(json.dumps(mr))
        else:
            print(f"title:\t{mr['title']}\nstate:\topen\nsource:\t{mr['source_branch']}\ntarget:\t{mr['target_branch']}\n"
                  f"url:\t{mr['web_url']}\n--\n{mr['description']}")
    elif verb == "diff":
        mr = MRS[number(rest)]
        print(git("diff", f"refs/heads/{mr['target_branch']}...refs/heads/{mr['source_branch']}"))
    else:
        sys.exit(f"{tool}: `{argv[0]} {verb}` is not available offline")


if __name__ == "__main__":
    main()

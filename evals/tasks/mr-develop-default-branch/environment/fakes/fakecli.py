#!/usr/bin/env python3
"""Offline stand-ins for `glab`, `gh` and the team's `tracker` CLI.

Installed under all three names; behaviour depends on the name it is invoked as.
State lives in /var/lib/fakes/state.json; every invocation is appended to
/var/log/fakes/calls.jsonl. Merge/pull requests created or edited are kept in the
state under "mrs" with the title, body, source/target branch and the source branch's
local and remote commit at the moment of creation.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

STATE = Path("/var/lib/fakes/state.json")
LOG = Path("/var/log/fakes/calls.jsonl")


def _load() -> dict:
    return json.loads(STATE.read_text())


def _save(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2))


def _log(tool: str, argv: list[str], **extra) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"at": datetime.now(UTC).isoformat(), "tool": tool, "cwd": os.getcwd(), "argv": argv, **extra}
    with LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def _read(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text()


def _git(*args: str, git_dir: str | None = None) -> str:
    cmd = ["git", f"--git-dir={git_dir}"] if git_dir else ["git"]
    out = subprocess.run([*cmd, *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def _default_branch(state: dict) -> str:
    return _git("symbolic-ref", "--short", "HEAD", git_dir=state["bare"]) or "main"


def _remote_sha(state: dict, branch: str) -> str:
    return _git("rev-parse", "--verify", "-q", f"refs/heads/{branch}", git_dir=state["bare"])


def _repo_json(state: dict) -> dict:
    default = _default_branch(state)
    return {
        "name": state["repo"].split("/")[-1],
        "nameWithOwner": state["repo"],
        "url": state["web"],
        "defaultBranchRef": {"name": default},
        "default_branch": default,
    }


# --- merge/pull request creation --------------------------------------------


def _create(tool: str, argv: list[str], parser: argparse.ArgumentParser, push_flag: bool) -> None:
    args, unknown = parser.parse_known_args(argv)
    state = _load()
    source = args.source or _git("rev-parse", "--abbrev-ref", "HEAD")
    if push_flag and getattr(args, "push", False):
        subprocess.run(["git", "push", "-u", "origin", source], check=False)
    title, body = args.title, None
    if args.body_file:
        body = _read(args.body_file)
    elif args.body is not None:
        body = sys.stdin.read() if args.body == "-" else args.body
    if args.fill and (title is None or body is None):
        log = _git("log", "--reverse", "--format=%s%n%n%b%x00", f"origin/{_default_branch(state)}..{source}")
        commits = [c.strip() for c in log.split("\x00") if c.strip()]
        title = title or (commits[0].splitlines()[0] if commits else source)
        body = body if body is not None else "\n\n".join(commits)
    if not title:
        sys.exit(f"{tool}: --title required when not running interactively")
    if body is None:
        body = ""
    remote = _remote_sha(state, source)
    local = _git("rev-parse", "--verify", "-q", source)
    record = {
        "tool": tool,
        "argv": argv,
        "unknown_flags": unknown,
        "title": title,
        "body": body,
        "source_branch": source,
        "target_branch": args.target or _default_branch(state),
        "target_explicit": args.target is not None,
        "draft": bool(args.draft),
        "local_sha_at_create": local,
        "remote_sha_at_create": remote,
    }
    _log(tool, argv, command="create", record=record)
    if not remote:
        sys.exit(
            f"{tool}: source branch '{source}' was not found on the remote; push the current branch first"
            + (" or use --push" if push_flag else "")
        )
    number = state["next_mr"]
    state["next_mr"] += 1
    record["number"] = number
    record["url"] = state["mr_url"].format(n=number)
    record["edits"] = []
    state["mrs"].append(record)
    _save(state)
    if tool == "glab":
        print(f"\nCreating merge request for {source} into {record['target_branch']} in {state['repo']}\n")
        print(f"!{number} {title} ({source})")
    print(record["url"])


def _find_mr(state: dict, ref: str | None) -> dict | None:
    if not state["mrs"]:
        return None
    if ref:
        ref = ref.lstrip("!#").rsplit("/", 1)[-1]
        for mr in state["mrs"]:
            if str(mr["number"]) == ref or mr["source_branch"] == ref:
                return mr
        return None
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    return next((m for m in reversed(state["mrs"]) if m["source_branch"] == branch), None)


def _edit(tool: str, argv: list[str], parser: argparse.ArgumentParser) -> None:
    args, _ = parser.parse_known_args(argv)
    state = _load()
    mr = _find_mr(state, args.ref)
    _log(tool, argv, command="edit")
    if mr is None:
        sys.exit(f"{tool}: no open merge request found")
    change = {}
    if args.title:
        change["title"] = args.title
    if args.body_file:
        change["body"] = _read(args.body_file)
    elif args.body is not None:
        change["body"] = args.body
    if args.target:
        change["target_branch"] = args.target
    mr.update(change)
    mr["edits"].append(change)
    _save(state)
    print(mr["url"])


def _view(tool: str, argv: list[str]) -> None:
    state = _load()
    ref = next((a for a in argv if not a.startswith("-")), None)
    mr = _find_mr(state, ref)
    _log(tool, argv, command="view")
    if mr is None:
        sys.exit(f"{tool}: no open merge request found for current branch")
    if "--json" in argv or "-F" in argv or "--output" in argv:
        print(json.dumps({"number": mr["number"], "url": mr["url"], "title": mr["title"], "body": mr["body"],
                          "baseRefName": mr["target_branch"], "headRefName": mr["source_branch"]}))
    else:
        print(f"{mr['title']}\n{mr['url']}\n\n{mr['body']}")


def _list(tool: str, argv: list[str]) -> None:
    state = _load()
    _log(tool, argv, command="list")
    if "--json" in argv:
        print(json.dumps([{"number": m["number"], "url": m["url"], "title": m["title"],
                           "headRefName": m["source_branch"]} for m in state["mrs"]]))
        return
    if not state["mrs"]:
        print("No open merge requests" if tool == "glab" else "no open pull requests")
    for m in state["mrs"]:
        print(f"!{m['number']}\t{m['title']}\t({m['source_branch']})")


def glab(argv: list[str]) -> None:
    state = _load()
    if argv[:2] == ["mr", "create"]:
        p = argparse.ArgumentParser(prog="glab mr create", add_help=False)
        p.add_argument("-t", "--title")
        p.add_argument("-d", "--description", dest="body")
        p.add_argument("--description-file", "-F", "--body-file", dest="body_file")
        p.add_argument("-b", "--target-branch", dest="target")
        p.add_argument("-s", "--source-branch", dest="source")
        p.add_argument("--draft", "--wip", action="store_true")
        p.add_argument("-f", "--fill", action="store_true")
        p.add_argument("--push", action="store_true")
        _create("glab", argv[2:], p, push_flag=True)
    elif argv[:2] in (["mr", "update"], ["mr", "edit"]):
        p = argparse.ArgumentParser(prog="glab mr update", add_help=False)
        p.add_argument("ref", nargs="?")
        p.add_argument("-t", "--title")
        p.add_argument("-d", "--description", dest="body")
        p.add_argument("--description-file", "-F", dest="body_file")
        p.add_argument("--target-branch", dest="target")
        _edit("glab", argv[2:], p)
    elif argv[:2] == ["mr", "view"]:
        _view("glab", argv[2:])
    elif argv[:2] == ["mr", "list"]:
        _list("glab", argv[2:])
    elif argv[:2] == ["repo", "view"]:
        _log("glab", argv, command="repo view")
        info = _repo_json(state)
        if "-F" in argv or "--output" in argv:
            print(json.dumps(info))
        else:
            print(f"name:\t{info['nameWithOwner']}\nurl:\t{info['url']}\ndefault branch:\t{info['default_branch']}")
    elif argv[:2] == ["auth", "status"]:
        _log("glab", argv, command="auth status")
        print(f"{state['host']}\n  ✓ Logged in to {state['host']} as dev")
    else:
        _log("glab", argv, command="unsupported")
        sys.exit(f"glab: unsupported in this environment: {' '.join(argv)}")


def gh(argv: list[str]) -> None:
    state = _load()
    if argv[:2] == ["pr", "create"]:
        p = argparse.ArgumentParser(prog="gh pr create", add_help=False)
        p.add_argument("-t", "--title")
        p.add_argument("-b", "--body", dest="body")
        p.add_argument("-F", "--body-file", "--description-file", dest="body_file")
        p.add_argument("-B", "--base", dest="target")
        p.add_argument("-H", "--head", dest="source")
        p.add_argument("-d", "--draft", action="store_true")
        p.add_argument("-f", "--fill", "--fill-first", "--fill-verbose", action="store_true")
        _create("gh", argv[2:], p, push_flag=False)
    elif argv[:2] == ["pr", "edit"]:
        p = argparse.ArgumentParser(prog="gh pr edit", add_help=False)
        p.add_argument("ref", nargs="?")
        p.add_argument("-t", "--title")
        p.add_argument("-b", "--body", dest="body")
        p.add_argument("-F", "--body-file", dest="body_file")
        p.add_argument("-B", "--base", dest="target")
        _edit("gh", argv[2:], p)
    elif argv[:2] == ["pr", "view"]:
        _view("gh", argv[2:])
    elif argv[:2] == ["pr", "list"]:
        _list("gh", argv[2:])
    elif argv[:2] == ["repo", "view"]:
        _log("gh", argv, command="repo view")
        info = _repo_json(state)
        if "--json" in argv:
            fields = argv[argv.index("--json") + 1].split(",") if len(argv) > argv.index("--json") + 1 else []
            out = {f: info[f] for f in fields if f in info} or info
            jq = next((argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-q", "--jq")), None)
            if jq and "defaultBranchRef" in jq:
                print(info["defaultBranchRef"]["name"])
            else:
                print(json.dumps(out))
        else:
            print(f"name:\t{info['nameWithOwner']}\ndescription:\t\n--\ndefault branch: {info['default_branch']}")
    elif argv[:1] == ["api"]:
        _log("gh", argv, command="api")
        path = next((a for a in argv[1:] if not a.startswith("-")), "")
        if path.rstrip("/").endswith(state["repo"]):
            print(json.dumps(_repo_json(state)))
        else:
            sys.exit(f"gh: HTTP 404: Not Found ({path})")
    elif argv[:2] == ["auth", "status"]:
        _log("gh", argv, command="auth status")
        print(f"{state['host']}\n  ✓ Logged in to {state['host']} account dev")
    else:
        _log("gh", argv, command="unsupported")
        sys.exit(f"gh: unsupported in this environment: {' '.join(argv)}")


# --- tracker ------------------------------------------------------------------


def tracker(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="tracker", description="Issue tracker CLI.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List tickets")
    sub.add_parser("statuses", help="List the board's workflow statuses, in order")
    search = sub.add_parser("search", help="Search ticket titles and descriptions")
    search.add_argument("query", nargs="+")
    show = sub.add_parser("show", help="Show a ticket's title, status, URL, description and links")
    show.add_argument("ticket")
    show.add_argument("--json", action="store_true")
    comments = sub.add_parser("comments", help="Show a ticket's comments")
    comments.add_argument("ticket")
    comment = sub.add_parser("comment", help="Add a comment to a ticket")
    comment.add_argument("ticket")
    comment.add_argument("--body")
    comment.add_argument("--body-file")
    link = sub.add_parser("link", help="Attach a link (e.g. a merge request URL) to a ticket")
    link.add_argument("ticket")
    link.add_argument("url")
    link.add_argument("--title")
    update = sub.add_parser("update", help="Change a ticket's status and/or title")
    update.add_argument("ticket")
    update.add_argument("--status")
    update.add_argument("--title")
    args = parser.parse_args(argv)
    write = args.command in {"comment", "link", "update"}
    _log("tracker", argv, command=args.command, write=write)

    state = _load()
    tickets = state["tickets"]
    if args.command == "list":
        for key, t in tickets.items():
            print(f"{key}\t{t['status']}\t{t['title']}")
        return
    if args.command == "statuses":
        print("\n".join(state["statuses"]))
        return
    if args.command == "search":
        words = [w.lower() for w in " ".join(args.query).split()]
        for key, t in tickets.items():
            hay = f"{key} {t['title']} {t['description']}".lower()
            if any(w in hay for w in words):
                print(f"{key}\t{t['status']}\t{t['title']}")
        return
    if args.ticket not in tickets:
        sys.exit(f"error: no ticket {args.ticket}")
    t = tickets[args.ticket]
    url = f"{state['tracker_url']}/{args.ticket}"
    if args.command == "show":
        if args.json:
            print(json.dumps({"id": args.ticket, "url": url, **{k: v for k, v in t.items() if k != "comments"}}, indent=2))
            return
        print(f"{args.ticket}: {t['title']}\nStatus: {t['status']}\nURL: {url}\n")
        print(t["description"])
        if t["links"]:
            print("\nLinks:")
            for ln in t["links"]:
                print(f"  {ln['url']}")
        if t["comments"]:
            print(f"\n({len(t['comments'])} comments: `tracker comments {args.ticket}`)")
    elif args.command == "comments":
        for c in t["comments"]:
            print(f"--- {c['author']} ({c['at']})\n{c['body']}\n")
    elif args.command == "comment":
        body = _read(args.body_file) if args.body_file else args.body
        if not body:
            sys.exit("error: give --body or --body-file")
        t["comments"].append({"author": "you", "at": datetime.now(UTC).isoformat(), "body": body})
        _save(state)
        print(f"Commented on {args.ticket}")
    elif args.command == "link":
        t["links"].append({"url": args.url, "title": args.title})
        _save(state)
        print(f"Linked {args.url} to {args.ticket}")
    elif args.command == "update":
        if args.status:
            match = next((s for s in state["statuses"] if s.lower() == args.status.lower()), None)
            if match is None:
                sys.exit(f"error: unknown status {args.status!r}; see `tracker statuses`")
            t["status"] = match
        if args.title:
            t["title"] = args.title
        _save(state)
        print(f"Updated {args.ticket}: {t['status']}")


if __name__ == "__main__":
    {"glab": glab, "gh": gh, "tracker": tracker}[Path(sys.argv[0]).name](sys.argv[1:])

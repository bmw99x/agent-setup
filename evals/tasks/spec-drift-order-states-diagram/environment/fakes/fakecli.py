#!/usr/bin/env python3
"""Offline stand-in for the team's issue tracker and wiki CLIs.

Installed as both ``tracker`` and ``wiki``; behaviour depends on the name it is invoked as.
State lives in /var/lib/fakes/state.json, uploads in /var/lib/fakes/uploads/, and every
invocation is appended to /var/log/fakes/calls.jsonl.
"""

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

STATE = Path("/var/lib/fakes/state.json")
UPLOADS = Path("/var/lib/fakes/uploads")
LOG = Path("/var/log/fakes/calls.jsonl")
TRACKER_HOST = "https://tracker.example.test"
WIKI_HOST = "https://wiki.example.test"


def _load() -> dict:
    return json.loads(STATE.read_text())


def _save(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2))


def _log(tool: str, argv: list[str], command: str, write: bool) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"at": datetime.now(UTC).isoformat(), "tool": tool, "command": command, "write": write, "argv": argv}
    with LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def _text(value: str | None, path: str | None) -> str:
    if path:
        return sys.stdin.read() if path == "-" else Path(path).read_text()
    if value is None:
        sys.exit("error: give the text inline or with a file option")
    return value


def _upload(state: dict, host: str, src: str) -> dict:
    source = Path(src)
    if not source.is_file():
        sys.exit(f"error: no such file: {src}")
    state["next_id"] += 1
    att_id = f"a-{state['next_id']}"
    UPLOADS.mkdir(parents=True, exist_ok=True)
    stored = UPLOADS / f"{att_id}-{source.name}"
    shutil.copyfile(source, stored)
    return {"id": att_id, "name": source.name, "url": f"{host}/attachments/{att_id}/{source.name}", "stored": str(stored)}


def tracker(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="tracker", description="Issue tracker CLI.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List tickets")
    show = sub.add_parser("show", help="Show a ticket's title, status, description and attachments")
    show.add_argument("ticket")
    show.add_argument("--json", action="store_true")
    comments = sub.add_parser("comments", help="Show a ticket's comments")
    comments.add_argument("ticket")
    update = sub.add_parser("update", help="Replace a ticket's description and/or title/status")
    update.add_argument("ticket")
    update.add_argument("--title")
    update.add_argument("--status")
    update.add_argument("--description")
    update.add_argument("--description-file", help="Read the new description from a file ('-' for stdin)")
    comment = sub.add_parser("comment", help="Add a comment to a ticket")
    comment.add_argument("ticket")
    comment.add_argument("--body")
    comment.add_argument("--body-file")
    attach = sub.add_parser("attach", help="Upload a file to a ticket; prints the attachment URL")
    attach.add_argument("ticket")
    attach.add_argument("file")
    args = parser.parse_args(argv)
    write = args.command in {"update", "comment", "attach"}
    _log("tracker", argv, args.command, write)

    state = _load()
    tickets = state["tickets"]
    if args.command == "list":
        for key, ticket in tickets.items():
            print(f"{key}\t{ticket['status']}\t{ticket['title']}")
        return
    if args.ticket not in tickets:
        sys.exit(f"error: no ticket {args.ticket}")
    ticket = tickets[args.ticket]
    if args.command == "show":
        if args.json:
            print(json.dumps({k: v for k, v in ticket.items() if k != "comments"}, indent=2))
            return
        print(f"{args.ticket}: {ticket['title']}\nStatus: {ticket['status']}\n")
        print(ticket["description"])
        if ticket["attachments"]:
            print("\nAttachments:")
            for att in ticket["attachments"]:
                print(f"  {att['id']}  {att['name']}  {att['url']}")
    elif args.command == "comments":
        for c in ticket["comments"]:
            print(f"--- {c['author']} ({c['at']})\n{c['body']}\n")
    elif args.command == "update":
        if args.description is not None or args.description_file:
            ticket["description"] = _text(args.description, args.description_file)
        if args.title:
            ticket["title"] = args.title
        if args.status:
            ticket["status"] = args.status
        _save(state)
        print(f"Updated {args.ticket}")
    elif args.command == "comment":
        ticket["comments"].append(
            {"author": "you", "at": datetime.now(UTC).isoformat(), "body": _text(args.body, args.body_file)}
        )
        _save(state)
        print(f"Commented on {args.ticket}")
    elif args.command == "attach":
        att = _upload(state, TRACKER_HOST, args.file)
        ticket["attachments"].append(att)
        _save(state)
        print(att["url"])


def wiki(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="wiki", description="Team wiki CLI.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List pages")
    show = sub.add_parser("show", help="Print a page's markdown body and attachments")
    show.add_argument("page")
    edit = sub.add_parser("edit", help="Replace a page's markdown body")
    edit.add_argument("page")
    edit.add_argument("--content")
    edit.add_argument("--file", help="Read the new body from a file ('-' for stdin)")
    attach = sub.add_parser("attach", help="Upload a file to a page; prints the file URL")
    attach.add_argument("page")
    attach.add_argument("file")
    args = parser.parse_args(argv)
    write = args.command in {"edit", "attach"}
    _log("wiki", argv, args.command, write)

    state = _load()
    pages = state["pages"]
    if args.command == "list":
        for key, page in pages.items():
            print(f"{key}\t{page['title']}")
        return
    if args.page not in pages:
        sys.exit(f"error: no page {args.page}")
    page = pages[args.page]
    if args.command == "show":
        print(f"# {page['title']}  ({WIKI_HOST}/{args.page})\n")
        print(page["body"])
        if page["attachments"]:
            print("\nAttachments:")
            for att in page["attachments"]:
                print(f"  {att['id']}  {att['name']}  {att['url']}")
    elif args.command == "edit":
        page["body"] = _text(args.content, args.file)
        _save(state)
        print(f"Saved {args.page}")
    elif args.command == "attach":
        att = _upload(state, WIKI_HOST, args.file)
        page["attachments"].append(att)
        _save(state)
        print(att["url"])


if __name__ == "__main__":
    {"tracker": tracker, "wiki": wiki}[Path(sys.argv[0]).name](sys.argv[1:])

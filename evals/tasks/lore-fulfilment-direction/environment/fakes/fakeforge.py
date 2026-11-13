#!/usr/bin/env python3
"""Offline, read-only stand-ins for `glab` and `gh` over a canned forge.

The forge (merge/pull requests, their diffs and review notes) is /opt/fakes/forge.json,
written at image build from the repo's real history. Every invocation is appended to
/var/log/fakes/calls.jsonl. Write commands are refused: this checkout is read-only on
the forge side.
"""

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

FORGE = Path("/opt/fakes/forge.json")
LOG = Path("/var/log/fakes/calls.jsonl")


def _log(tool: str, argv: list[str], command: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as fh:
            fh.write(json.dumps({"at": datetime.now(UTC).isoformat(), "tool": tool, "cwd": os.getcwd(),
                                 "argv": argv, "command": command}) + "\n")
    except OSError:
        pass


def _forge() -> dict:
    return json.loads(FORGE.read_text())


def _flag(argv: list[str], *names: str) -> str | None:
    for i, a in enumerate(argv):
        for n in names:
            if a == n and i + 1 < len(argv):
                return argv[i + 1]
            if a.startswith(n + "="):
                return a.split("=", 1)[1]
    return None


def _has(argv: list[str], *names: str) -> bool:
    return any(a in names for a in argv)


def _positional(argv: list[str], value_flags: set[str]) -> list[str]:
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a.startswith("-"):
            if a in value_flags:
                skip = True
            continue
        out.append(a)
    return out


def _emit(data, argv: list[str]) -> None:
    text = json.dumps(data, indent=2)
    jq = _flag(argv, "--jq", "-q")
    if jq:
        out = subprocess.run(["jq", "-r", jq], input=text, capture_output=True, text=True)
        sys.stdout.write(out.stdout)
        if out.returncode:
            sys.exit(out.stderr.strip())
        return
    print(text)


def _mr(forge: dict, ref: str | None) -> dict:
    if ref is None:
        sys.exit("error: give a merge request number")
    ref = ref.lstrip("!#").rstrip("/").rsplit("/", 1)[-1]
    for mr in forge["mrs"]:
        if str(mr["number"]) == ref or mr["source_branch"] == ref:
            return mr
    sys.exit(f"error: no merge request {ref} in {forge['repo']}")


def _name(forge: dict, user: str) -> str:
    return forge["people"].get(user, user)


def _split_diff(diff: str) -> list[dict]:
    files = []
    for chunk in re.split(r"(?m)^(?=diff --git )", diff):
        if not chunk.strip():
            continue
        m = re.match(r"diff --git a/(\S+) b/(\S+)", chunk)
        old, new = (m.group(1), m.group(2)) if m else ("", "")
        body = chunk.split("\n@@", 1)
        files.append({"old_path": old, "new_path": new, "new_file": "new file mode" in chunk.split("@@")[0],
                      "deleted_file": "deleted file mode" in chunk.split("@@")[0],
                      "diff": ("@@" + body[1]) if len(body) > 1 else ""})
    return files


# --- GitLab ---------------------------------------------------------------------


def _gl_user(forge: dict, user: str) -> dict:
    return {"username": user, "name": _name(forge, user)}


def _gl_mr(forge: dict, mr: dict) -> dict:
    return {
        "iid": mr["number"], "id": 9000 + mr["number"], "project_id": 42,
        "title": mr["title"], "description": mr["description"], "state": mr["state"],
        "draft": mr["draft"], "work_in_progress": mr["draft"],
        "author": _gl_user(forge, mr["author"]),
        "merged_by": _gl_user(forge, mr["merged_by"]) if mr.get("merged_by") else None,
        "created_at": mr["created_at"], "updated_at": mr["updated_at"], "merged_at": mr.get("merged_at"),
        "source_branch": mr["source_branch"], "target_branch": mr["target_branch"],
        "merge_commit_sha": mr.get("merge_commit_sha"), "labels": mr.get("labels", []),
        "user_notes_count": len(mr["notes"]),
        "web_url": f"{forge['web']}/-/merge_requests/{mr['number']}",
    }


def _gl_note(forge: dict, note: dict) -> dict:
    out = {"id": note["id"], "type": "DiffNote" if note.get("path") else None, "body": note["body"],
           "author": _gl_user(forge, note["author"]), "created_at": note["created_at"],
           "updated_at": note["created_at"], "system": False, "resolvable": bool(note.get("path")),
           "resolved": bool(note.get("path"))}
    if note.get("path"):
        out["position"] = {"new_path": note["path"], "old_path": note["path"], "new_line": note.get("line")}
    return out


def _gl_select(forge: dict, state: str, author: str | None, draft: bool | None) -> list[dict]:
    mrs = [m for m in forge["mrs"] if state in ("all", m["state"])]
    if author:
        mrs = [m for m in mrs if m["author"] == author.lstrip("@")]
    if draft is not None:
        mrs = [m for m in mrs if m["draft"] == draft]
    return sorted(mrs, key=lambda m: m["created_at"], reverse=True)


def _gl_api(forge: dict, argv: list[str]) -> None:
    path = next((a for a in argv if not a.startswith("-")), "")
    url = urlparse(path)
    query = {k: v[-1] for k, v in parse_qs(url.query).items()}
    parts = [unquote(p) for p in url.path.strip("/").split("/")]
    if parts[:1] == ["api"]:
        parts = parts[2:]
    # projects/<id>/merge_requests[/<iid>[/notes|/discussions|/changes|/diffs|/commits]]
    if len(parts) >= 3 and parts[0] == "projects" and parts[2] == "merge_requests":
        if len(parts) == 3:
            draft = {"yes": True, "no": False}.get(query.get("wip", ""))
            state = {"opened": "opened", "merged": "merged", "closed": "closed"}.get(query.get("state", "all"), "all")
            _emit([_gl_mr(forge, m) for m in _gl_select(forge, state, query.get("author_username"), draft)], argv)
            return
        mr = _mr(forge, parts[3])
        tail = parts[4] if len(parts) > 4 else ""
        if tail == "":
            _emit(_gl_mr(forge, mr), argv)
        elif tail == "notes":
            _emit([_gl_note(forge, n) for n in mr["notes"]], argv)
        elif tail == "discussions":
            _emit([{"id": f"d{n['id']}", "individual_note": not n.get("path"), "notes": [_gl_note(forge, n)]}
                   for n in mr["notes"]], argv)
        elif tail == "changes":
            _emit({**_gl_mr(forge, mr), "changes": _split_diff(mr["diff"])}, argv)
        elif tail == "diffs":
            _emit(_split_diff(mr["diff"]), argv)
        elif tail == "commits":
            _emit([{"id": c["sha"], "short_id": c["sha"][:8], "title": c["title"], "author_name": _name(forge, c["author"]),
                    "created_at": c["at"]} for c in mr["commits"]], argv)
        else:
            sys.exit(f"glab: 404 Not Found ({path})")
        return
    if len(parts) == 2 and parts[0] == "projects":
        _emit({"id": 42, "path_with_namespace": forge["repo"], "default_branch": "main", "web_url": forge["web"]}, argv)
        return
    sys.exit(f"glab: 404 Not Found ({path})")


def glab(argv: list[str]) -> None:
    forge = _forge()
    as_json = (_flag(argv, "-F", "--output", "-O") or "").lower() == "json"
    if argv[:2] == ["mr", "list"]:
        _log("glab", argv, "mr list")
        rest = argv[2:]
        state = "merged" if _has(rest, "--merged", "-M") else "closed" if _has(rest, "--closed", "-c") \
            else "all" if _has(rest, "--all", "-A") else "opened"
        if (s := _flag(rest, "--state", "-s")):
            state = {"open": "opened", "opened": "opened", "merged": "merged", "closed": "closed"}.get(s, "all")
        draft = True if _has(rest, "--draft", "-d") else False if _has(rest, "--not-draft") else None
        mrs = _gl_select(forge, state, _flag(rest, "--author"), draft)
        if as_json:
            _emit([_gl_mr(forge, m) for m in mrs], rest)
            return
        label = {"opened": "open", "all": ""}.get(state, state)
        print(f"Showing {len(mrs)} {label} merge requests on {forge['repo']}.\n".replace("  ", " "))
        for m in mrs:
            print(f"!{m['number']}\t{forge['repo']}!{m['number']}\t{m['title']}\t({m['target_branch']}) ← ({m['source_branch']})")
    elif argv[:2] == ["mr", "view"]:
        _log("glab", argv, "mr view")
        rest = argv[2:]
        mr = _mr(forge, next(iter(_positional(rest, {"-F", "--output", "-O", "-R", "--repo"})), None))
        comments = _has(rest, "--comments", "-c")
        if as_json:
            data = _gl_mr(forge, mr)
            if comments:
                data["Notes"] = [_gl_note(forge, n) for n in mr["notes"]]
            _emit(data, rest)
            return
        print(f"title:\t{mr['title']}\nstate:\t{mr['state']}{' (draft)' if mr['draft'] else ''}\n"
              f"author:\t{mr['author']} ({_name(forge, mr['author'])})\ncreated:\t{mr['created_at']}\n"
              f"merged:\t{mr.get('merged_at') or '-'}\nsource:\t{mr['source_branch']}\ntarget:\t{mr['target_branch']}\n"
              f"url:\t{forge['web']}/-/merge_requests/{mr['number']}\n--\n{mr['description']}\n")
        if comments:
            print(f"--\n{len(mr['notes'])} comments\n")
            for n in mr["notes"]:
                where = f" on {n['path']}:{n.get('line')}" if n.get("path") else ""
                print(f"{n['author']} commented {n['created_at']}{where}\n{n['body']}\n")
        elif mr["notes"]:
            print(f"({len(mr['notes'])} comments; use --comments to show them)")
    elif argv[:2] == ["mr", "diff"]:
        _log("glab", argv, "mr diff")
        mr = _mr(forge, next(iter(_positional(argv[2:], {"-R", "--repo", "--color"})), None))
        sys.stdout.write(mr["diff"])
    elif argv[:2] in (["mr", "note"], ["mr", "create"], ["mr", "update"], ["mr", "merge"], ["mr", "approve"]):
        _log("glab", argv, "refused")
        sys.exit("glab: this token is read-only (403 Forbidden)")
    elif argv[:1] == ["api"]:
        _log("glab", argv, "api")
        if _flag(argv, "-X", "--method") not in (None, "GET"):
            sys.exit("glab: this token is read-only (403 Forbidden)")
        _gl_api(forge, argv[1:])
    elif argv[:2] == ["repo", "view"]:
        _log("glab", argv, "repo view")
        print(f"name:\t{forge['repo']}\nurl:\t{forge['web']}\ndefault branch:\tmain")
    elif argv[:2] == ["auth", "status"]:
        _log("glab", argv, "auth status")
        print(f"{forge['host']}\n  ✓ Logged in to {forge['host']} as dev (read-only token)")
    else:
        _log("glab", argv, "unsupported")
        sys.exit(f"glab: unsupported in this environment: {' '.join(argv)}\n"
                 "supported: mr list, mr view [--comments], mr diff, api projects/:id/merge_requests[/<iid>/notes|discussions|changes|commits], repo view")


# --- GitHub ---------------------------------------------------------------------


GH_STATE = {"opened": "OPEN", "merged": "MERGED", "closed": "CLOSED"}


def _gh_user(forge: dict, user: str) -> dict:
    return {"login": user, "name": _name(forge, user)}


def _gh_comment(forge: dict, note: dict) -> dict:
    body = f"`{note['path']}:{note.get('line')}` {note['body']}" if note.get("path") else note["body"]
    return {"author": _gh_user(forge, note["author"]), "body": body, "createdAt": note["created_at"]}


def _gh_pr(forge: dict, mr: dict) -> dict:
    return {
        "number": mr["number"], "title": mr["title"], "body": mr["description"], "state": GH_STATE[mr["state"]],
        "isDraft": mr["draft"], "author": _gh_user(forge, mr["author"]),
        "createdAt": mr["created_at"], "updatedAt": mr["updated_at"], "mergedAt": mr.get("merged_at"),
        "closedAt": mr.get("merged_at"), "mergedBy": _gh_user(forge, mr["merged_by"]) if mr.get("merged_by") else None,
        "headRefName": mr["source_branch"], "baseRefName": mr["target_branch"],
        "url": f"{forge['web']}/pull/{mr['number']}", "labels": [{"name": n} for n in mr.get("labels", [])],
        "mergeCommit": {"oid": mr["merge_commit_sha"]} if mr.get("merge_commit_sha") else None,
        "comments": [_gh_comment(forge, n) for n in mr["notes"]],
        "reviews": [{"author": _gh_user(forge, n["author"]), "body": _gh_comment(forge, n)["body"], "state": "COMMENTED",
                     "submittedAt": n["created_at"]} for n in mr["notes"] if n.get("path")],
        "files": [{"path": f["new_path"] or f["old_path"]} for f in _split_diff(mr["diff"])],
        "commits": [{"oid": c["sha"], "messageHeadline": c["title"], "authoredDate": c["at"],
                     "authors": [_gh_user(forge, c["author"])]} for c in mr["commits"]],
    }


def _gh_fields(data: dict, argv: list[str]) -> dict:
    fields = _flag(argv, "--json")
    if not fields:
        return data
    return {f: data.get(f) for f in fields.split(",")}


def _gh_select(forge: dict, state: str, author: str | None, draft: bool | None) -> list[dict]:
    want = {"open": ["opened"], "merged": ["merged"], "closed": ["closed", "merged"], "all": ["opened", "merged", "closed"]}[state]
    mrs = [m for m in forge["mrs"] if m["state"] in want]
    if author:
        mrs = [m for m in mrs if m["author"] == author.lstrip("@")]
    if draft is not None:
        mrs = [m for m in mrs if m["draft"] == draft]
    return sorted(mrs, key=lambda m: m["created_at"], reverse=True)


def _gh_rest_pr(forge: dict, mr: dict) -> dict:
    return {"number": mr["number"], "title": mr["title"], "body": mr["description"],
            "state": "open" if mr["state"] == "opened" else "closed", "draft": mr["draft"],
            "user": {"login": mr["author"]}, "created_at": mr["created_at"], "merged_at": mr.get("merged_at"),
            "head": {"ref": mr["source_branch"]}, "base": {"ref": mr["target_branch"]},
            "html_url": f"{forge['web']}/pull/{mr['number']}", "merge_commit_sha": mr.get("merge_commit_sha")}


def _gh_api(forge: dict, argv: list[str]) -> None:
    path = next((a for a in argv if not a.startswith("-") and argv[argv.index(a) - 1] not in ("--jq", "-q", "-X", "--method", "-H", "--header")), "")
    url = urlparse(path)
    query = {k: v[-1] for k, v in parse_qs(url.query).items()}
    parts = url.path.strip("/").split("/")
    repo = "/".join(parts[1:3]) if parts[:1] == ["repos"] else ""
    if repo and repo not in (forge["repo"], "{owner}/{repo}", ":owner/:repo"):
        sys.exit(f"gh: Not Found (HTTP 404) ({path})")
    rest = parts[3:]
    if rest == []:
        _emit({"full_name": forge["repo"], "default_branch": "main", "html_url": forge["web"]}, argv)
    elif rest == ["pulls"]:
        state = query.get("state", "open")
        mrs = _gh_select(forge, {"open": "open", "closed": "closed", "all": "all"}.get(state, "open"), None, None)
        _emit([_gh_rest_pr(forge, m) for m in mrs], argv)
    elif len(rest) >= 2 and rest[0] in ("pulls", "issues"):
        mr = _mr(forge, rest[1])
        tail = rest[2] if len(rest) > 2 else ""
        if tail == "":
            _emit(_gh_rest_pr(forge, mr), argv)
        elif rest[0] == "pulls" and tail == "comments":
            _emit([{"id": n["id"], "user": {"login": n["author"]}, "body": n["body"], "path": n["path"],
                    "line": n.get("line"), "created_at": n["created_at"]} for n in mr["notes"] if n.get("path")], argv)
        elif rest[0] == "pulls" and tail == "reviews":
            _emit([{"id": n["id"], "user": {"login": n["author"]}, "body": "", "state": "COMMENTED",
                    "submitted_at": n["created_at"]} for n in mr["notes"] if n.get("path")], argv)
        elif rest[0] == "issues" and tail == "comments":
            _emit([{"id": n["id"], "user": {"login": n["author"]}, "body": n["body"], "created_at": n["created_at"]}
                   for n in mr["notes"] if not n.get("path")], argv)
        elif rest[0] == "pulls" and tail == "files":
            _emit([{"filename": f["new_path"], "patch": f["diff"]} for f in _split_diff(mr["diff"])], argv)
        elif rest[0] == "pulls" and tail == "commits":
            _emit([{"sha": c["sha"], "commit": {"message": c["title"], "author": {"name": _name(forge, c["author"]), "date": c["at"]}}}
                   for c in mr["commits"]], argv)
        else:
            sys.exit(f"gh: Not Found (HTTP 404) ({path})")
    else:
        sys.exit(f"gh: Not Found (HTTP 404) ({path})")


def gh(argv: list[str]) -> None:
    forge = _forge()
    if argv[:2] == ["pr", "list"]:
        _log("gh", argv, "pr list")
        rest = argv[2:]
        state = (_flag(rest, "--state", "-s") or "open").lower()
        draft = True if _has(rest, "--draft", "-d") else None
        mrs = _gh_select(forge, state if state in ("open", "merged", "closed", "all") else "open", _flag(rest, "--author", "-A"), draft)
        limit = int(_flag(rest, "--limit", "-L") or 30)
        mrs = mrs[:limit]
        if _flag(rest, "--json"):
            _emit([_gh_fields(_gh_pr(forge, m), rest) for m in mrs], rest)
            return
        for m in mrs:
            print(f"#{m['number']}\t{m['title']}\t{m['source_branch']}\t{GH_STATE[m['state']]}{' DRAFT' if m['draft'] else ''}\t{m['created_at']}")
    elif argv[:2] == ["pr", "view"]:
        _log("gh", argv, "pr view")
        rest = argv[2:]
        mr = _mr(forge, next(iter(_positional(rest, {"--json", "--jq", "-q", "-R", "--repo", "-t", "--template"})), None))
        if _flag(rest, "--json"):
            _emit(_gh_fields(_gh_pr(forge, mr), rest), rest)
            return
        print(f"title:\t{mr['title']}\nstate:\t{GH_STATE[mr['state']]}{' (draft)' if mr['draft'] else ''}\n"
              f"author:\t{mr['author']}\ncreated:\t{mr['created_at']}\nmerged:\t{mr.get('merged_at') or '-'}\n"
              f"url:\t{forge['web']}/pull/{mr['number']}\n--\n{mr['description']}\n")
        if _has(rest, "--comments", "-c"):
            for n in mr["notes"]:
                c = _gh_comment(forge, n)
                print(f"{n['author']} • {n['created_at']}\n{c['body']}\n")
        elif mr["notes"]:
            print(f"({len(mr['notes'])} comments; use --comments to show them)")
    elif argv[:2] == ["pr", "diff"]:
        _log("gh", argv, "pr diff")
        mr = _mr(forge, next(iter(_positional(argv[2:], {"-R", "--repo", "--color"})), None))
        sys.stdout.write(mr["diff"])
    elif argv[:2] in (["pr", "comment"], ["pr", "create"], ["pr", "edit"], ["pr", "merge"], ["pr", "review"]):
        _log("gh", argv, "refused")
        sys.exit("gh: this token is read-only (HTTP 403)")
    elif argv[:1] == ["api"]:
        _log("gh", argv, "api")
        if _flag(argv, "-X", "--method") not in (None, "GET"):
            sys.exit("gh: this token is read-only (HTTP 403)")
        _gh_api(forge, argv[1:])
    elif argv[:2] == ["repo", "view"]:
        _log("gh", argv, "repo view")
        if _flag(argv, "--json"):
            _emit(_gh_fields({"name": forge["repo"].split("/")[-1], "nameWithOwner": forge["repo"], "url": forge["web"],
                              "defaultBranchRef": {"name": "main"}}, argv), argv)
        else:
            print(f"name:\t{forge['repo']}\n--\ndefault branch: main")
    elif argv[:2] == ["auth", "status"]:
        _log("gh", argv, "auth status")
        print(f"{forge['host']}\n  ✓ Logged in to {forge['host']} account dev (read-only token)")
    else:
        _log("gh", argv, "unsupported")
        sys.exit(f"gh: unsupported in this environment: {' '.join(argv)}\n"
                 "supported: pr list, pr view [--comments|--json], pr diff, api repos/:owner/:repo/pulls[/<n>/comments|reviews|files|commits], "
                 "api repos/:owner/:repo/issues/<n>/comments, repo view")


if __name__ == "__main__":
    {"glab": glab, "gh": gh}[Path(sys.argv[0]).name](sys.argv[1:])

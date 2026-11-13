#!/usr/bin/env python3
"""Offline stand-ins for `glab` and `gh`, serving one merge/pull request's review threads.

Installed under both names; behaviour depends on the name it is invoked as. State lives in
/var/lib/fakes/state.json (see seed.py); every invocation is appended to /var/log/fakes/calls.jsonl.
Writes the verifier reads are kept in the state:

* ``replies``  -- a note added to an existing review thread (thread id, body, time, remote head then)
* ``resolves`` -- a thread marked resolved
* ``general``  -- a top-level MR/PR comment or a new discussion (not a reply to a thread)

Supported, GitLab: ``glab api`` (MR, discussions, notes, project), ``glab mr view|list|diff|note``.
Supported, GitHub: ``gh api graphql`` (pullRequest, reviewThreads, reply/resolve mutations),
``gh api`` REST (pulls, review comments + replies, issue comments), ``gh pr view|list|diff|comment``.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl

STATE = Path("/var/lib/fakes/state.json")
LOG = Path("/var/log/fakes/calls.jsonl")


def _load() -> dict:
    return json.loads(STATE.read_text())


def _save(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2))


def _log(tool: str, argv: list[str], **extra) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps({"at": time.time(), "tool": tool, "cwd": os.getcwd(), "argv": argv, **extra}) + "\n")


def _git_bare(state: dict, *args: str) -> str:
    out = subprocess.run(["git", f"--git-dir={state['bare']}", *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def _remote_sha(state: dict, branch: str) -> str:
    return _git_bare(state, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())


def _die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def _emit(obj, jq: str | None = None) -> None:
    text = json.dumps(obj, indent=2)
    if jq:
        out = subprocess.run(["jq", "-r", jq], input=text, capture_output=True, text=True)
        sys.stdout.write(out.stdout)
        if out.returncode:
            _die(out.stderr.strip(), out.returncode)
    else:
        print(text)


def _mr(state: dict, ref) -> dict | None:
    ref = str(ref).lstrip("!#").rstrip("/").rsplit("/", 1)[-1] if ref is not None else None
    for mr in state["mrs"]:
        if ref is None or str(mr["number"]) == ref or mr["source_branch"] == ref:
            return mr
    return None


def _current_mr(state: dict) -> dict | None:
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
    return next((m for m in state["mrs"] if m["source_branch"] == branch), None)


def _thread(state: dict, thread_id: str) -> dict | None:
    return next((t for t in state["threads"] if t["id"] == thread_id), None)


def _thread_of_comment(state: dict, comment_id) -> dict | None:
    for t in state["threads"]:
        if any(str(n["id"]) == str(comment_id) or n.get("node_id") == comment_id for n in t["notes"]):
            return t
    return None


def _record_reply(state: dict, thread: dict, body: str, how: str) -> dict:
    mr = _mr(state, thread["mr"])
    note_id = state["next_note"]
    state["next_note"] += 1
    note = {"id": note_id, "node_id": f"PRRC_reply{note_id}", "author": state["me"], "body": body,
            "created_at": _now_iso(), "reply": True}
    thread["notes"].append(note)
    state["replies"].append({"thread": thread["id"], "body": body, "at": time.time(), "how": how,
                             "remote_head": _remote_sha(state, mr["source_branch"])})
    _save(state)
    return note


def _record_resolve(state: dict, thread: dict, resolved: bool, how: str) -> None:
    thread["resolved"] = resolved
    state["resolves"].append({"thread": thread["id"], "resolved": resolved, "at": time.time(), "how": how})
    _save(state)


def _record_general(state: dict, mr: dict, body: str, how: str) -> dict:
    note_id = state["next_note"]
    state["next_note"] += 1
    state["general"].append({"mr": mr["number"], "id": note_id, "body": body, "at": time.time(), "how": how})
    _save(state)
    return {"id": note_id, "body": body, "author": {"username": state["me"], "login": state["me"]},
            "created_at": _now_iso()}


def _parse_fields(argv: list[str]) -> tuple[list[str], dict, dict]:
    """Split `api` argv into positional args, flags and -f/-F fields (typed like gh/glab do)."""
    pos, flags, fields = [], {}, {}
    i = 0
    takes_value = {"-X", "--method", "-H", "--header", "-q", "--jq", "--input", "-t", "--template",
                   "--hostname", "-R", "--repo", "--cache", "-p", "--preview"}
    while i < len(argv):
        a = argv[i]
        if a in ("-f", "--raw-field", "-F", "--field"):
            k, _, v = argv[i + 1].partition("=")
            if a in ("-F", "--field"):
                if v.startswith("@"):
                    v = sys.stdin.read() if v == "@-" else Path(v[1:]).read_text()
                elif v in ("true", "false"):
                    v = v == "true"
                elif re.fullmatch(r"-?\d+", v):
                    v = int(v)
            fields[k] = v
            i += 2
        elif a.startswith("--") and "=" in a:
            k, _, v = a.partition("=")
            flags[k] = v
            i += 1
        elif a in takes_value:
            flags[a] = argv[i + 1]
            i += 2
        elif a.startswith("-"):
            flags[a] = True
            i += 1
        else:
            pos.append(a)
            i += 1
    if "--input" in flags:
        raw = sys.stdin.read() if flags["--input"] == "-" else Path(flags["--input"]).read_text()
        try:
            fields.update(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return pos, flags, fields


def _opts(argv: list[str], value_flags: set[str]) -> tuple[list[str], dict]:
    pos, flags = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--") and "=" in a:
            k, _, v = a.partition("=")
            flags[k] = v
        elif a in value_flags and i + 1 < len(argv):
            flags[a] = argv[i + 1]
            i += 1
        elif a.startswith("-"):
            flags[a] = True
        else:
            pos.append(a)
        i += 1
    return pos, flags


def _method(flags: dict, fields: dict) -> str:
    m = flags.get("-X") or flags.get("--method")
    return m.upper() if m else ("POST" if fields else "GET")


# --- GitLab -------------------------------------------------------------------------------------


def _gl_note(state: dict, n: dict, resolvable: bool, resolved: bool, kind: str) -> dict:
    return {
        "id": n["id"], "type": kind, "body": n["body"], "attachment": None,
        "author": {"id": 7, "username": n["author"], "name": n["author"].title()},
        "created_at": n["created_at"], "updated_at": n["created_at"], "system": n.get("system", False),
        "noteable_type": "MergeRequest", "resolvable": resolvable, "resolved": resolved if resolvable else False,
        "resolved_by": ({"username": n.get("resolved_by", "author")} if resolvable and resolved else None),
        **({"position": n["position"]} if "position" in n else {}),
    }


def _gl_discussion(state: dict, t: dict) -> dict:
    resolvable = t.get("resolvable", True)
    kind = "DiffNote" if t.get("path") else ("DiscussionNote" if resolvable else None)
    notes = []
    for i, n in enumerate(t["notes"]):
        n = dict(n)
        if i == 0 and t.get("path"):
            n["position"] = {"base_sha": t["base_sha"], "start_sha": t["base_sha"], "head_sha": t["head_sha"],
                             "position_type": "text", "old_path": t["path"], "new_path": t["path"],
                             "old_line": None, "new_line": t["line"]}
        notes.append(_gl_note(state, n, resolvable, t.get("resolved", False), kind))
    return {"id": t["id"], "individual_note": t.get("individual_note", False), "notes": notes}


def _gl_mr(state: dict, mr: dict) -> dict:
    sha = _remote_sha(state, mr["source_branch"])
    return {
        "id": 9000 + mr["number"], "iid": mr["number"], "project_id": 42, "title": mr["title"],
        "description": mr["body"], "state": "opened", "draft": False,
        "source_branch": mr["source_branch"], "target_branch": mr["target_branch"],
        "author": {"username": state["me"]}, "sha": sha,
        "diff_refs": {"base_sha": _remote_sha(state, mr["target_branch"]), "head_sha": sha,
                      "start_sha": _remote_sha(state, mr["target_branch"])},
        "web_url": state["mr_url"].format(n=mr["number"]),
        "references": {"short": f"!{mr['number']}", "full": f"{state['repo']}!{mr['number']}"},
        "user_notes_count": sum(len(t["notes"]) for t in state["threads"] if t["mr"] == mr["number"]),
        "blocking_discussions_resolved": all(t.get("resolved") for t in state["threads"]
                                             if t["mr"] == mr["number"] and t.get("resolvable", True)),
        "has_conflicts": False, "merge_status": "can_be_merged", "detailed_merge_status": "discussions_not_resolved",
    }


def glab_api(argv: list[str]) -> None:
    pos, flags, fields = _parse_fields(argv)
    if not pos:
        _die("glab api: endpoint required")
    state = _load()
    endpoint, _, query = pos[0].lstrip("/").removeprefix("api/v4/").partition("?")
    fields = {**dict(parse_qsl(query)), **fields}
    method = _method(flags, {k: v for k, v in fields.items() if k not in dict(parse_qsl(query))})
    _log("glab", ["api", *argv], command="api", method=method, endpoint=endpoint)

    m = re.fullmatch(r"projects/[^/]+(?:/(.*))?", endpoint)
    if not m:
        if endpoint in ("user",):
            return _emit({"id": 7, "username": state["me"]})
        _die(f"glab: 404 Not Found ({endpoint})")
    rest = m.group(1) or ""
    if rest == "":
        return _emit({"id": 42, "path_with_namespace": state["repo"], "web_url": state["web"],
                      "default_branch": "main", "ssh_url_to_repo": state["clone"]})
    if rest == "merge_requests":
        mrs = [_gl_mr(state, mr) for mr in state["mrs"]]
        if "source_branch" in fields:
            mrs = [x for x in mrs if x["source_branch"] == fields["source_branch"]]
        if "target_branch" in fields:
            mrs = [x for x in mrs if x["target_branch"] == fields["target_branch"]]
        return _emit(mrs)
    m = re.fullmatch(r"merge_requests/(\d+)(?:/(.*))?", rest)
    if not m or not _mr(state, m.group(1)):
        _die(f"glab: 404 Not Found ({endpoint})")
    mr = _mr(state, m.group(1))
    sub = m.group(2) or ""
    threads = [t for t in state["threads"] if t["mr"] == mr["number"]]
    body = fields.get("body")
    if sub == "" and method == "GET":
        return _emit(_gl_mr(state, mr))
    if sub == "discussions" and method == "GET":
        return _emit([_gl_discussion(state, t) for t in threads])
    if sub == "discussions" and method == "POST":
        note = _record_general(state, mr, body or "", "glab api POST discussions")
        return _emit({"id": f"new{note['id']}", "individual_note": False, "notes": [note]})
    if sub == "notes" and method == "GET":
        return _emit([n for t in threads for n in _gl_discussion(state, t)["notes"]])
    if sub == "notes" and method == "POST":
        return _emit(_record_general(state, mr, body or "", "glab api POST notes"))
    if sub in ("changes", "diffs"):
        diff = _git_bare(state, "diff", f"{mr['target_branch']}...{mr['source_branch']}")
        return _emit({"changes": [{"diff": diff}]} if sub == "changes" else [{"diff": diff}])
    if sub == "commits":
        log = _git_bare(state, "log", "--format=%H%x09%s", f"{mr['target_branch']}..{mr['source_branch']}")
        return _emit([{"id": ln.split("\t")[0], "title": ln.split("\t")[1]} for ln in log.splitlines()])
    m = re.fullmatch(r"discussions/([^/]+)(?:/notes(?:/(\d+))?)?", sub)
    if m:
        t = next((t for t in threads if t["id"] == m.group(1)), None)
        if t is None:
            _die(f"glab: 404 Discussion Not Found ({endpoint})")
        is_notes = "/notes" in sub
        if method == "GET":
            return _emit(_gl_discussion(state, t) if not is_notes else _gl_discussion(state, t)["notes"])
        if method == "POST" and is_notes and not m.group(2):
            note = _record_reply(state, t, body or "", "glab api POST discussions/:id/notes")
            return _emit(_gl_note(state, note, t.get("resolvable", True), t.get("resolved", False), "DiffNote"))
        if method == "PUT" and "resolved" in fields:
            _record_resolve(state, t, str(fields["resolved"]).lower() == "true", f"glab api PUT {sub}")
            return _emit(_gl_discussion(state, t))
        if method == "PUT" and m.group(2) and body is not None:
            return _emit({"id": int(m.group(2)), "body": body})
    _die(f"glab: 404 Not Found ({method} {endpoint})")


def _gl_comments_text(state: dict, mr: dict) -> str:
    out = []
    for t in state["threads"]:
        if t["mr"] != mr["number"]:
            continue
        for i, n in enumerate(t["notes"]):
            where = f" on {t['path']}:{t['line']}" if t.get("path") and i == 0 else ""
            flag = " (resolved)" if t.get("resolved") and i == 0 else ""
            out.append(f"{n['author']} commented{where}{flag}\n  {n['body']}\n")
    return "\n".join(out)


def glab(argv: list[str]) -> None:
    if argv[:1] == ["api"]:
        return glab_api(argv[1:])
    state = _load()
    _log("glab", argv, command=" ".join(argv[:2]))
    if argv[:2] == ["mr", "view"]:
        ref = next((a for a in argv[2:] if not a.startswith("-") and a not in ("json",)), None)
        mr = _mr(state, ref) if ref else _current_mr(state)
        if mr is None:
            _die("no open merge request available for current branch")
        info = _gl_mr(state, mr)
        if any(a in argv for a in ("-F", "--output")) and "json" in argv:
            if "--comments" in argv or "-c" in argv:
                info["Notes"] = [n for t in state["threads"] if t["mr"] == mr["number"]
                                 for n in _gl_discussion(state, t)["notes"]]
            return _emit(info)
        print(f"title:\t{mr['title']}\nstate:\topen\nauthor:\t{state['me']}\nsource:\t{mr['source_branch']}\n"
              f"target:\t{mr['target_branch']}\nurl:\t{info['web_url']}\n--\n{mr['body']}\n")
        if "--comments" in argv or "-c" in argv:
            print(_gl_comments_text(state, mr))
        return
    if argv[:2] == ["mr", "list"]:
        mrs = [_gl_mr(state, mr) for mr in state["mrs"]]
        if any(a in argv for a in ("-F", "--output")) and "json" in argv:
            return _emit(mrs)
        print(f"Showing {len(mrs)} open merge requests on {state['repo']}.\n")
        for x in mrs:
            print(f"!{x['iid']}\t{state['repo']}!{x['iid']}\t{x['title']}\t({x['target_branch']}) ← ({x['source_branch']})")
        return
    if argv[:2] == ["mr", "diff"]:
        ref = next((a for a in argv[2:] if not a.startswith("-")), None)
        mr = _mr(state, ref) if ref else _current_mr(state)
        print(_git_bare(state, "diff", f"{mr['target_branch']}...{mr['source_branch']}"))
        return
    if argv[:2] in (["mr", "note"], ["mr", "comment"]):
        ref = None
        msg = None
        rest = argv[2:]
        i = 0
        while i < len(rest):
            if rest[i] in ("-m", "--message"):
                msg = rest[i + 1]
                i += 2
            elif rest[i].startswith("--message="):
                msg = rest[i].split("=", 1)[1]
                i += 1
            elif rest[i].startswith("-"):
                i += 1
            else:
                ref = rest[i]
                i += 1
        mr = _mr(state, ref) if ref else _current_mr(state)
        if mr is None or msg is None:
            _die("glab mr note: give the MR and -m <message>")
        _record_general(state, mr, msg, "glab mr note")
        print(state["mr_url"].format(n=mr["number"]) + "#note_" + str(state["next_note"] - 1))
        return
    if argv[:2] == ["auth", "status"]:
        print(f"{state['host']}\n  ✓ Logged in to {state['host']} as {state['me']}")
        return
    if argv[:2] == ["repo", "view"]:
        print(f"name:\t{state['repo']}\nurl:\t{state['web']}\ndefault branch:\tmain")
        return
    _die(f"glab: unsupported in this environment: {' '.join(argv)}")


# --- GitHub -------------------------------------------------------------------------------------


def _gh_comment_rest(state: dict, t: dict, n: dict, first: dict) -> dict:
    return {
        "id": n["id"], "node_id": n["node_id"], "pull_request_review_id": 5000 + first["id"],
        "path": t["path"], "line": t["line"], "original_line": t["line"], "side": "RIGHT",
        "commit_id": t["head_sha"], "original_commit_id": t["head_sha"], "body": n["body"],
        "user": {"login": n["author"]}, "created_at": n["created_at"], "updated_at": n["created_at"],
        "html_url": f"{state['mr_url'].format(n=t['mr'])}#discussion_r{n['id']}",
        **({"in_reply_to_id": first["id"]} if n is not first else {}),
    }


def _gh_comment_gql(state: dict, t: dict, n: dict) -> dict:
    return {"id": n["node_id"], "databaseId": n["id"], "body": n["body"], "author": {"login": n["author"]},
            "createdAt": n["created_at"], "path": t["path"], "line": t["line"], "originalLine": t["line"],
            "outdated": False, "url": f"{state['mr_url'].format(n=t['mr'])}#discussion_r{n['id']}"}


def _gh_thread_gql(state: dict, t: dict) -> dict:
    nodes = [_gh_comment_gql(state, t, n) for n in t["notes"]]
    return {"id": t["id"], "isResolved": t.get("resolved", False), "isOutdated": False, "isCollapsed": False,
            "path": t["path"], "line": t["line"], "originalLine": t["line"], "startLine": None,
            "diffSide": "RIGHT", "subjectType": "LINE",
            "resolvedBy": {"login": t["notes"][0]["author"]} if t.get("resolved") else None,
            "comments": {"totalCount": len(nodes), "nodes": nodes, "pageInfo": {"hasNextPage": False, "endCursor": None}}}


def _gh_pr_gql(state: dict, mr: dict) -> dict:
    threads = [_gh_thread_gql(state, t) for t in state["threads"] if t["mr"] == mr["number"]]
    general = [{"id": f"IC_{g['id']}", "databaseId": g["id"], "body": g["body"], "author": {"login": state["me"]}}
               for g in state["general"] if g["mr"] == mr["number"]]
    return {"id": f"PR_kwDOpr{mr['number']}", "number": mr["number"], "title": mr["title"], "body": mr["body"],
            "state": "OPEN", "url": state["mr_url"].format(n=mr["number"]),
            "headRefName": mr["source_branch"], "headRefOid": _remote_sha(state, mr["source_branch"]),
            "baseRefName": mr["target_branch"], "author": {"login": state["me"]},
            "reviewDecision": "CHANGES_REQUESTED",
            "reviewThreads": {"totalCount": len(threads), "nodes": threads,
                              "pageInfo": {"hasNextPage": False, "endCursor": None}},
            "comments": {"totalCount": len(general), "nodes": general,
                         "pageInfo": {"hasNextPage": False, "endCursor": None}},
            "reviews": {"nodes": [{"author": {"login": r["author"]}, "state": r["state"], "body": r["body"]}
                                  for r in state.get("reviews", [])]}}


def _gql_arg(text: str, name: str, variables: dict):
    m = re.search(rf"\b{name}\s*:\s*(\$\w+|\"((?:[^\"\\]|\\.)*)\"|\d+)", text)
    if not m:
        return None
    tok = m.group(1)
    if tok.startswith("$"):
        return variables.get(tok[1:])
    if tok.startswith('"'):
        return json.loads(tok)
    return int(tok)


def gh_graphql(fields: dict, jq: str | None) -> None:
    state = _load()
    query = fields.pop("query", "")
    variables = {**fields, **(fields.pop("variables", {}) if isinstance(fields.get("variables"), dict) else {})}
    if re.search(r"^\s*mutation\b", query, re.S):
        tid = _gql_arg(query, "pullRequestReviewThreadId", variables) or _gql_arg(query, "threadId", variables)
        if "addPullRequestReviewThreadReply" in query:
            t = _thread(state, tid)
            if t is None:
                _die(f"gh: Could not resolve to a node with the global id of '{tid}'")
            note = _record_reply(state, t, _gql_arg(query, "body", variables) or "", "graphql addPullRequestReviewThreadReply")
            return _emit({"data": {"addPullRequestReviewThreadReply": {"comment": _gh_comment_gql(state, t, note)}}}, jq)
        if "addPullRequestReviewComment" in query:
            t = _thread_of_comment(state, _gql_arg(query, "inReplyTo", variables))
            if t is None:
                _die("gh: inReplyTo comment not found")
            note = _record_reply(state, t, _gql_arg(query, "body", variables) or "", "graphql addPullRequestReviewComment")
            return _emit({"data": {"addPullRequestReviewComment": {"comment": _gh_comment_gql(state, t, note)}}}, jq)
        if "unresolveReviewThread" in query or "resolveReviewThread" in query:
            t = _thread(state, tid)
            if t is None:
                _die(f"gh: Could not resolve to a node with the global id of '{tid}'")
            resolved = "unresolveReviewThread" not in query
            _record_resolve(state, t, resolved, "graphql resolveReviewThread")
            key = "resolveReviewThread" if resolved else "unresolveReviewThread"
            return _emit({"data": {key: {"thread": {"id": t["id"], "isResolved": resolved}}}}, jq)
        if "addComment" in query:
            mr = state["mrs"][0]
            note = _record_general(state, mr, _gql_arg(query, "body", variables) or "", "graphql addComment")
            return _emit({"data": {"addComment": {"commentEdge": {"node": {"id": f"IC_{note['id']}"}}}}}, jq)
        _die("gh: this fake supports addPullRequestReviewThreadReply, addPullRequestReviewComment, "
             "resolveReviewThread and addComment mutations")
    number = _gql_arg(query, "number", variables)
    mr = _mr(state, number) if number is not None else state["mrs"][0]
    if mr is None:
        _die(f"gh: Could not resolve to a PullRequest with the number of {number}.")
    pr = _gh_pr_gql(state, mr)
    owner, name = state["repo"].split("/")
    data = {"repository": {"name": name, "owner": {"login": owner}, "nameWithOwner": state["repo"], "pullRequest": pr},
            "viewer": {"login": state["me"]}}
    m = re.search(r"\bnode\s*\(\s*id\s*:\s*(\$\w+|\"[^\"]+\")", query)
    if m:
        nid = variables.get(m.group(1)[1:]) if m.group(1).startswith("$") else json.loads(m.group(1))
        t = _thread(state, nid)
        data["node"] = _gh_thread_gql(state, t) if t else pr
    return _emit({"data": data}, jq)


def gh_api(argv: list[str]) -> None:
    pos, flags, fields = _parse_fields(argv)
    jq = flags.get("-q") or flags.get("--jq")
    if not pos:
        _die("gh api: endpoint required")
    state = _load()
    owner, name = state["repo"].split("/")
    endpoint, _, query = pos[0].lstrip("/").replace("{owner}", owner).replace("{repo}", name).partition("?")
    method = _method(flags, fields)
    _log("gh", ["api", *argv], command="api", method=method, endpoint=endpoint)
    if endpoint == "graphql":
        return gh_graphql(fields, jq)
    if endpoint == "user":
        return _emit({"login": state["me"]}, jq)
    m = re.fullmatch(r"repos/([^/]+)/([^/]+)(?:/(.*))?", endpoint)
    if not m or f"{m.group(1)}/{m.group(2)}" != state["repo"]:
        _die(f"gh: Not Found (HTTP 404) ({endpoint})")
    rest = m.group(3) or ""
    if rest == "":
        return _emit({"name": name, "full_name": state["repo"], "default_branch": "main", "html_url": state["web"]}, jq)
    if rest == "pulls":
        return _emit([_gh_pr_rest(state, mr) for mr in state["mrs"]], jq)
    m = re.fullmatch(r"(pulls|issues)/(\d+)(?:/(.*))?", rest)
    mr = _mr(state, m.group(2)) if m else None
    if mr is None:
        _die(f"gh: Not Found (HTTP 404) ({endpoint})")
    kind, sub = m.group(1), m.group(3) or ""
    threads = [t for t in state["threads"] if t["mr"] == mr["number"]]
    if kind == "pulls" and sub == "":
        return _emit(_gh_pr_rest(state, mr), jq)
    if kind == "pulls" and sub == "comments" and method == "GET":
        return _emit([_gh_comment_rest(state, t, n, t["notes"][0]) for t in threads for n in t["notes"]], jq)
    if kind == "pulls" and sub == "comments" and method == "POST":
        t = _thread_of_comment(state, fields.get("in_reply_to"))
        if t is None:
            _die("gh: Validation Failed (HTTP 422): new review comments need a commit_id, path and line")
        note = _record_reply(state, t, fields.get("body", ""), "REST POST pulls/:n/comments in_reply_to")
        return _emit(_gh_comment_rest(state, t, note, t["notes"][0]), jq)
    mm = re.fullmatch(r"comments/(\d+)/replies", sub)
    if kind == "pulls" and mm and method == "POST":
        t = _thread_of_comment(state, mm.group(1))
        if t is None:
            _die("gh: Not Found (HTTP 404)")
        note = _record_reply(state, t, fields.get("body", ""), "REST POST pulls/:n/comments/:id/replies")
        return _emit(_gh_comment_rest(state, t, note, t["notes"][0]), jq)
    if kind == "pulls" and sub == "reviews":
        return _emit([{"id": 7000 + i, "user": {"login": r["author"]}, "state": r["state"], "body": r["body"]}
                      for i, r in enumerate(state.get("reviews", []))], jq)
    if kind == "pulls" and sub == "files":
        files = _git_bare(state, "diff", "--name-only", f"{mr['target_branch']}...{mr['source_branch']}")
        return _emit([{"filename": f} for f in files.splitlines()], jq)
    if kind == "issues" and sub == "comments" and method == "GET":
        return _emit([{"id": g["id"], "body": g["body"], "user": {"login": state["me"]}}
                      for g in state["general"] if g["mr"] == mr["number"]], jq)
    if kind == "issues" and sub == "comments" and method == "POST":
        return _emit(_record_general(state, mr, fields.get("body", ""), "REST POST issues/:n/comments"), jq)
    _die(f"gh: Not Found (HTTP 404) ({method} {endpoint})")


def _gh_pr_rest(state: dict, mr: dict) -> dict:
    return {"number": mr["number"], "title": mr["title"], "body": mr["body"], "state": "open",
            "html_url": state["mr_url"].format(n=mr["number"]), "user": {"login": state["me"]},
            "head": {"ref": mr["source_branch"], "sha": _remote_sha(state, mr["source_branch"])},
            "base": {"ref": mr["target_branch"], "sha": _remote_sha(state, mr["target_branch"])}}


def gh(argv: list[str]) -> None:
    if argv[:1] == ["api"]:
        return gh_api(argv[1:])
    state = _load()
    _log("gh", argv, command=" ".join(argv[:2]))
    pos, flags = _opts(argv[2:], {"--json", "-q", "--jq", "-b", "--body", "-F", "--body-file", "-R", "--repo",
                                  "-t", "--template", "-s", "--state", "-L", "--limit", "-H", "--head", "-B", "--base"})
    jq = flags.get("-q") or flags.get("--jq")
    if argv[:2] == ["pr", "view"]:
        mr = _mr(state, pos[0]) if pos else _current_mr(state)
        if mr is None:
            _die("no pull requests found for branch")
        pr = _gh_pr_gql(state, mr)
        if "--json" in flags:
            want = str(flags["--json"]).split(",")
            pr["comments"] = pr["comments"]["nodes"]
            pr["reviews"] = pr["reviews"]["nodes"]
            pr.pop("reviewThreads")
            return _emit({k: pr[k] for k in want if k in pr}, jq)
        print(f"{mr['title']} #{mr['number']}\nOpen • {state['me']} wants to merge into {mr['target_branch']} "
              f"from {mr['source_branch']}\n\n{mr['body']}\n\nView this pull request on GitHub: {pr['url']}")
        if "--comments" in flags or "-c" in flags:
            for r in state.get("reviews", []):
                print(f"\n{r['author']} requested changes\n  {r['body']}")
        return
    if argv[:2] == ["pr", "list"]:
        prs = [_gh_pr_gql(state, mr) for mr in state["mrs"]]
        if "--json" in flags:
            want = str(flags["--json"]).split(",")
            return _emit([{k: p[k] for k in want if k in p} for p in prs], jq)
        for p in prs:
            print(f"#{p['number']}\t{p['title']}\t{p['headRefName']}\tOPEN")
        return
    if argv[:2] == ["pr", "diff"]:
        mr = _mr(state, pos[0]) if pos else _current_mr(state)
        print(_git_bare(state, "diff", f"{mr['target_branch']}...{mr['source_branch']}"))
        return
    if argv[:2] == ["pr", "comment"]:
        mr = _mr(state, pos[0]) if pos else _current_mr(state)
        body = flags.get("-b") or flags.get("--body")
        if body is None and ("-F" in flags or "--body-file" in flags):
            src = flags.get("-F") or flags.get("--body-file")
            body = sys.stdin.read() if src == "-" else Path(src).read_text()
        _record_general(state, mr, str(body or ""), "gh pr comment")
        print(state["mr_url"].format(n=mr["number"]) + "#issuecomment-1")
        return
    if argv[:2] == ["auth", "status"]:
        print(f"{state['host']}\n  ✓ Logged in to {state['host']} account {state['me']}")
        return
    if argv[:2] == ["repo", "view"]:
        print(f"name:\t{state['repo']}\n--\ndefault branch: main")
        return
    _die(f"gh: unsupported in this environment: {' '.join(argv)}")


if __name__ == "__main__":
    {"glab": glab, "gh": gh}[Path(sys.argv[0]).name](sys.argv[1:])

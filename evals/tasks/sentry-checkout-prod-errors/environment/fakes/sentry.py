#!/usr/bin/env python3
"""Offline stand-in for the `sentry` CLI (cli.sentry.dev, v0.34).

Commands and flags come from spec.json, generated from the CLI's own reference docs, so an
unknown command or flag fails the way the real tool does (exit 20, "No flag registered").
Data lives in /var/lib/fakes/sentry-state.json (timestamps stored as seconds-ago and rendered
against the current clock). Every invocation is appended to /var/log/fakes/sentry-calls.jsonl
with the resolved target, the exit code and any mutation it made.
"""

import difflib
import fnmatch
import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

STATE = Path("/var/lib/fakes/sentry-state.json")
LOG = Path("/var/log/fakes/sentry-calls.jsonl")
SPEC = json.loads(Path(os.environ.get("SENTRY_FAKE_SPEC", "/usr/local/share/sentry-fake/spec.json")).read_text())
VERSION = "0.34.0"
NOW = datetime.now(UTC)
ALIASES = {"issue reopen": "issue unresolve", "issue ignore": "issue archive"}
GLOBAL_FLAGS = {
    "json": {"short": None, "value": False},
    "fields": {"short": None, "value": True},
    "help": {"short": "h", "value": False},
    "log-level": {"short": None, "value": True},
    "verbose": {"short": None, "value": False},
    "version": {"short": "V", "value": False},
}
RECORD: dict = {}


class CliError(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


def input_error(msg: str) -> CliError:
    return CliError(msg, 20)


# ---------------------------------------------------------------- state & time


def load() -> dict:
    return json.loads(STATE.read_text())


def save(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=1))


def at(ago: float) -> datetime:
    return NOW - timedelta(seconds=ago)


def iso(ago: float | None) -> str | None:
    return None if ago is None else at(ago).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def humanize(ago: float) -> str:
    for unit, secs in (("day", 86400), ("hour", 3600), ("minute", 60)):
        if ago >= secs:
            n = int(ago // secs)
            return f"{n} {unit}{'s' if n != 1 else ''} ago"
    return "just now"


DURATION = re.compile(r"^(\d+)\s*(s|m|min|h|d|w)$")
UNIT_SECS = {"s": 1, "m": 60, "min": 60, "h": 3600, "d": 86400, "w": 604800}


def duration(text: str) -> int | None:
    m = DURATION.match(text.strip())
    return int(m.group(1)) * UNIT_SECS[m.group(2)] if m else None


def parse_date(text: str) -> datetime | None:
    try:
        d = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def period_window(text: str) -> tuple[datetime, datetime]:
    """(start, end) for --period: '24h', '7d', 'a..b', '>=date', '<=date'."""
    secs = duration(text)
    if secs is not None:
        return NOW - timedelta(seconds=secs), NOW
    if ".." in text:
        a, b = text.split("..", 1)
        da, db = parse_date(a) if a else datetime.min.replace(tzinfo=UTC), parse_date(b) if b else NOW
        if da and db:
            return da, db
    m = re.match(r"^(>=|<=|>|<)(.+)$", text)
    if m and parse_date(m.group(2)):
        d = parse_date(m.group(2))
        return (d, NOW) if m.group(1).startswith(">") else (datetime.min.replace(tzinfo=UTC), d)
    raise input_error(
        f'Invalid period "{text}". Use a relative duration (e.g. "24h", "7d", "90d"), '
        'a range ("2026-04-01..2026-05-01") or a bound (">=2026-04-01").'
    )


# ---------------------------------------------------------------- argv parsing


def resolve_command(argv: list[str]) -> tuple[str, list[str]]:
    words: list[str] = []
    i = 0
    while i < len(argv) and not argv[i].startswith("-"):
        cand = " ".join([*words, argv[i]])
        cand = ALIASES.get(cand, cand)
        if cand in SPEC or any(k.startswith(cand + " ") for k in SPEC):
            words = cand.split(" ")
            i += 1
            if cand in SPEC and not any(k.startswith(cand + " ") for k in SPEC):
                break
            continue
        break
    path = " ".join(words)
    if path in SPEC:
        return path, argv[i:]
    rest = argv[i:]
    if "--help" in rest or "-h" in rest or not rest:
        return path, rest
    word = rest[0]
    choices = sorted({k[len(path):].strip().split(" ")[0] for k in SPEC if k.startswith(path)})
    hint = difflib.get_close_matches(word, choices, n=1)
    where = f"sentry {path}".strip()
    msg = f"No command registered for `{word}`" + (f"\nDid you mean `{hint[0]}`?" if hint else "")
    msg += f"\nRun `{where} --help` to see available commands."
    raise input_error(msg)


def parse_flags(path: str, args: list[str]) -> tuple[dict, list[str]]:
    flags = {**GLOBAL_FLAGS, **(SPEC[path]["flags"] if path in SPEC else {})}
    shorts = {v["short"]: k for k, v in flags.items() if v.get("short")}
    opts: dict = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            positional += args[i + 1:]
            break
        if a.startswith("--") or (a.startswith("-") and len(a) > 1 and not re.match(r"^-\d", a)):
            if a.startswith("--"):
                name, _, inline = a[2:].partition("=")
                has_inline = "=" in a
            else:
                if a[1] not in shorts:
                    raise input_error(f"No flag registered for -{a[1]}")
                name, inline, has_inline = shorts[a[1]], a[2:], len(a) > 2
            if name not in flags:
                hint = difflib.get_close_matches(name, list(flags), n=1)
                raise input_error(f"No flag registered for --{name}" + (f"\nDid you mean --{hint[0]}?" if hint else ""))
            spec = flags[name]
            if spec["value"]:
                if has_inline:
                    val = inline
                else:
                    if i + 1 >= len(args):
                        raise input_error(f"Expected input for flag --{name}")
                    i += 1
                    val = args[i]
                if spec.get("multi"):
                    opts.setdefault(name, []).append(val)
                else:
                    opts[name] = val
            else:
                if has_inline:
                    raise input_error(f"Flag --{name} does not take a value")
                opts[name] = True
        else:
            positional.append(a)
        i += 1
    for k, v in flags.items():
        if k not in opts and v.get("default") is not None:
            opts[k] = v["default"]
    return opts, positional


def print_help(path: str) -> None:
    if path in SPEC:
        s = SPEC[path]
        print(f"USAGE\n  sentry {path} {s['args']}\n\n{s['desc']}\n\nFLAGS")
        for name, f in s["flags"].items():
            short = f"-{f['short']}, " if f["short"] else "    "
            val = " <value>" if f["value"] else ""
            default = f' (default: "{f["default"]}")' if f.get("default") else ""
            print(f"  {short}--{name}{val}  {f['help']}{default}")
        print("      --json  Output as JSON\n      --fields <value>  Comma-separated JSON fields to include")
        print("  -h, --help  Print help information and exit")
        return
    subs = sorted({k[len(path):].strip().split(" ")[0] for k in SPEC if k.startswith(path)})
    print(f"USAGE\n  sentry {path + ' ' if path else ''}<command>\n\nCOMMANDS")
    for sub in subs:
        full = f"{path} {sub}".strip()
        desc = SPEC[full]["desc"] if full in SPEC else ""
        print(f"  {sub:<14} {desc}")
    print("\nGLOBAL FLAGS\n  --help, --version, --log-level <level>, --verbose")


# ---------------------------------------------------------------- output


def select_fields(obj, fields: str | None):
    if not fields:
        return obj
    names = [f.strip() for f in fields.replace(" ", ",").split(",") if f.strip()]

    def pick(o: dict) -> dict:
        out = {}
        for n in names:
            cur = o
            for part in n.split("."):
                cur = cur.get(part) if isinstance(cur, dict) else None
            if n in o:
                cur = o[n]
            out[n] = cur
        return out

    return [pick(o) for o in obj] if isinstance(obj, list) else pick(obj)


def wants_json(opts: dict) -> bool:
    return bool(opts.get("json") or opts.get("fields"))


def emit_json(obj, opts: dict) -> None:
    print(json.dumps(select_fields(obj, opts.get("fields")), indent=2))


def table(rows: list[list[str]], headers: list[str]) -> None:
    widths = [max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip())
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip())


def note(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------------------------------------------------------------- targets


def find_org(state: dict, slug: str) -> dict:
    for o in state["orgs"]:
        if o["slug"] == slug:
            return o
    raise CliError(f"Organization '{slug}' not found (404). Run `sentry org list` to see organizations you can access.", 30)


def find_project(state: dict, org: str, slug: str) -> dict:
    find_org(state, org)
    for p in state["projects"]:
        if p["org"] == org and p["slug"] == slug:
            return p
    raise CliError(f"Project '{slug}' not found in organization '{org}' (404).", 30)


def _detect(state: dict) -> tuple[dict, str] | None:
    env_org, env_proj = os.environ.get("SENTRY_ORG"), os.environ.get("SENTRY_PROJECT")
    if env_org and env_proj:
        return find_project(state, env_org, env_proj), "SENTRY_ORG/SENTRY_PROJECT"
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        rc = d / ".sentryclirc"
        if rc.is_file():
            vals = dict(re.findall(r"^\s*(org|project)\s*=\s*(\S+)", rc.read_text(), re.M))
            if "org" in vals and "project" in vals:
                return find_project(state, vals["org"], vals["project"]), f"{rc}"
    dsn = re.compile(r"https://([0-9a-f]+)@o(\d+)\.ingest\.[\w.]*sentry\.io/(\d+)")
    env_files = [f for d in [cwd, *cwd.parents] for f in sorted(d.glob(".env*")) if f.is_file()]
    candidates = env_files + sorted(p for p in cwd.rglob("*.py") if ".venv" not in p.parts)[:200]
    for f in candidates:
        try:
            m = dsn.search(f.read_text(errors="ignore"))
        except OSError:
            continue
        if m:
            for p in state["projects"]:
                if p["id"] == m.group(3):
                    return p, f"DSN in {f}"
    for p in state["projects"]:
        if p["slug"] == cwd.name:
            return p, "directory name"
    return None


def resolve_projects(state: dict, target: str | None) -> list[dict]:
    """Projects a list command covers: 'org/project', 'org/', bare 'project', or auto-detected."""
    if target:
        if "/" in target:
            org, _, proj = target.partition("/")
            if not proj:
                find_org(state, org)
                projs = [p for p in state["projects"] if p["org"] == org]
            else:
                projs = [find_project(state, org, proj)]
        else:
            projs = [p for p in state["projects"] if p["slug"] == target]
            if not projs:
                raise CliError(f"No project '{target}' found in any of your organizations.", 30)
        RECORD["resolved"] = sorted(f"{p['org']}/{p['slug']}" for p in projs)
        return projs
    found = _detect(state)
    if not found:
        raise input_error(
            "Could not auto-detect organization and project.\n"
            "Specify the target explicitly: sentry <command> <org>/<project>"
        )
    proj, source = found
    note(f"Using {proj['org']}/{proj['slug']} (detected from {source})")
    RECORD["resolved"] = [f"{proj['org']}/{proj['slug']}"]
    RECORD["detected"] = True
    return [proj]


def find_issue(state: dict, ref: str) -> dict:
    raw = ref.strip()
    m = re.search(r"/issues/(\d+)", raw)
    if m:
        raw = m.group(1)
    if "/" in raw:
        org, _, raw = raw.partition("/")
        find_org(state, org)
    for issue in state["issues"]:
        if raw == issue["id"] or raw.upper() == issue["shortId"].upper():
            RECORD.setdefault("issues", []).append(issue["shortId"])
            return issue
    raise CliError(f"Issue '{ref}' not found (404).", 30)


# ---------------------------------------------------------------- issues


def issue_json(state: dict, issue: dict) -> dict:
    proj = next(p for p in state["projects"] if p["slug"] == issue["project"])
    return {
        "id": issue["id"],
        "shortId": issue["shortId"],
        "title": issue["title"],
        "culprit": issue["culprit"],
        "count": str(issue["count"]),
        "userCount": issue["userCount"],
        "firstSeen": iso(issue["firstSeenAgo"]),
        "lastSeen": iso(issue["lastSeenAgo"]),
        "level": issue["level"],
        "status": issue["status"],
        "statusDetails": issue.get("statusDetails", {}),
        "substatus": issue.get("substatus"),
        "permalink": f"https://{proj['org']}.sentry.io/issues/{issue['id']}/",
        "project": {"id": proj["id"], "slug": proj["slug"], "name": proj["slug"], "platform": proj["platform"]},
        "metadata": issue.get("metadata", {}),
        "assignedTo": issue.get("assignedTo"),
        "priority": issue.get("priority", "medium"),
        "platform": proj["platform"],
        "isUnhandled": issue.get("isUnhandled", True),
        "seerFixabilityScore": None,
        "type": "error",
    }


QTOKEN = re.compile(r'(!?)([\w.\-]+):("[^"]*"|\[[^\]]*\]|\S+)|"([^"]*)"|(\S+)')


def _match_value(pattern: str, values: list[str]) -> bool:
    pattern = pattern.strip('"')
    alts = [p.strip() for p in pattern[1:-1].split(",")] if pattern.startswith("[") else [pattern]
    return any(fnmatch.fnmatch(str(v).lower(), alt.lower()) for v in values for alt in alts)


def _time_match(value: str, ago: float) -> bool:
    m = re.match(r"^(>=|<=|>|<)?(.+)$", value)
    op, val = m.group(1), m.group(2)
    rel = re.match(r"^([+-]?)(\d+\s*(?:s|m|min|h|d|w))$", val)
    if rel:
        secs = duration(rel.group(2))
        older = rel.group(1) == "+" or op in ("<", "<=")
        return ago >= secs if older else ago <= secs
    d = parse_date(val)
    if not d:
        raise CliError(f"Invalid date value for search: {value} (400)", 30)
    when = at(ago)
    return when >= d if op in (None, ">", ">=") else when <= d


def _status_match(issue: dict, value: str) -> bool:
    v = value.lower()
    if v in ("unresolved", "resolved"):
        return issue["status"] == v
    if v in ("ignored", "archived"):
        return issue["status"] == "ignored"
    if v == "unassigned":
        return not issue.get("assignedTo")
    if v == "assigned":
        return bool(issue.get("assignedTo"))
    if v in ("new", "regressed", "escalating", "ongoing", "for_review"):
        return issue.get("substatus") == v or (v == "for_review" and issue["status"] == "unresolved")
    raise CliError(f'Invalid value for "is" search: {value} (400)', 30)


def _term_match(issue: dict, key: str, value: str) -> bool:
    k = key.lower()
    if k == "is":
        return _status_match(issue, value)
    if k in ("firstseen", "age", "first_seen"):
        return _time_match(value, issue["firstSeenAgo"])
    if k in ("lastseen", "last_seen"):
        return _time_match(value, issue["lastSeenAgo"])
    if k in ("times_seen", "timesseen"):
        m = re.match(r"^(>=|<=|>|<)?(\d+)$", value)
        if not m:
            raise CliError(f"Invalid number for times_seen: {value} (400)", 30)
        n, c = int(m.group(2)), int(issue["count"])
        return {">": c > n, ">=": c >= n, "<": c < n, "<=": c <= n, None: c == n}[m.group(1)]
    if k == "level":
        return _match_value(value, [issue["level"]])
    if k in ("issue.priority", "priority"):
        return _match_value(value, [issue.get("priority", "medium")])
    if k in ("assigned", "assigned_to", "bookmarks", "subscribed"):
        return False
    if k == "has":
        return True
    if k in ("message", "title"):
        return _match_value(value if "*" in value else f"*{value}*", [issue["title"]])
    if k in ("error.type",):
        return _match_value(value, [issue.get("metadata", {}).get("type", "")])
    if k in ("error.value",):
        return _match_value(value, [issue.get("metadata", {}).get("value", "")])
    if k == "project":
        return _match_value(value, [issue["project"]])
    tags = issue.get("tags", {})
    if k == "env":
        k = "environment"
    return _match_value(value, list(tags.get(k, {}).keys()))


def filter_issues(issues: list[dict], query: str) -> list[dict]:
    tokens = QTOKEN.findall(query)
    for neg, key, val, quoted, word in tokens:
        if word in ("OR", "AND"):
            raise CliError(
                'Error parsing search query: Boolean statements containing "OR" or "AND" are not supported in this search (400)',
                30,
            )
    out = []
    for issue in issues:
        ok = True
        for neg, key, val, quoted, word in tokens:
            if key:
                hit = _term_match(issue, key, val.strip('"'))
                hit = not hit if neg else hit
            else:
                text = (quoted or word).lower()
                hay = f"{issue['title']} {issue['culprit']}".lower()
                hit = fnmatch.fnmatch(hay, f"*{text}*")
            if not hit:
                ok = False
                break
        if ok:
            out.append(issue)
    return out


SORTS = {
    "date": lambda i: i["lastSeenAgo"],
    "new": lambda i: i["firstSeenAgo"],
    "freq": lambda i: -int(i["count"]),
    "user": lambda i: -i["userCount"],
}


def query_issues(state: dict, projs: list[dict], query: str, sort: str, period: str) -> list[dict]:
    if sort not in SORTS:
        raise input_error(f'Invalid sort "{sort}". Must be one of: date, new, freq, user')
    start, end = period_window(period)
    slugs = {p["slug"] for p in projs}
    issues = [i for i in state["issues"] if i["project"] in slugs and i.get("merged_into") is None]
    issues = [i for i in issues if at(i["lastSeenAgo"]) >= start and at(i["firstSeenAgo"]) <= end]
    issues = filter_issues(issues, query)
    return sorted(issues, key=SORTS[sort])


def paginate(state: dict, key: str, items: list, limit: int, cursor: str | None) -> tuple[list, bool]:
    cursors = state.setdefault("cursors", {})
    offset = cursors.get(key, 0)
    if cursor in (None, "first"):
        offset = 0
    elif cursor == "next":
        offset += limit
    elif cursor == "prev":
        offset = max(0, offset - limit)
    else:
        m = re.match(r"^\d+:(\d+):\d+$", cursor)
        if not m:
            raise input_error(f'Invalid cursor "{cursor}"')
        offset = int(m.group(1))
    cursors[key] = offset
    save(state)
    return items[offset:offset + limit], offset + limit < len(items)


def parse_limit(text: str, hi: int = 1000) -> int:
    if not str(text).isdigit() or not 1 <= int(text) <= hi:
        raise input_error(f'Invalid limit "{text}": expected an integer between 1 and {hi}')
    return int(text)


def cmd_issue_list(state, opts, pos):
    if len(pos) > 1:
        raise input_error("Too many arguments. Expected at most 1: <org/project>")
    projs = resolve_projects(state, pos[0] if pos else None)
    query = opts.get("query", "is:unresolved")
    issues = query_issues(state, projs, query, opts["sort"], opts["period"])
    limit = parse_limit(opts["limit"])
    key = json.dumps(["issue list", sorted(p["slug"] for p in projs), query, opts["sort"], opts["period"], limit])
    page, more = paginate(state, key, issues, limit, opts.get("cursor"))
    RECORD["returned"] = [i["shortId"] for i in page]
    if wants_json(opts):
        emit_json([issue_json(state, i) for i in page], opts)
    elif not page:
        print("No issues found.")
    else:
        rows = [[i["level"], i["shortId"], f"{int(i['count']):,}", str(i["userCount"]), humanize(i["lastSeenAgo"]),
                 humanize(i["firstSeenAgo"]), i["title"][:72]] for i in page]
        table(rows, ["LEVEL", "SHORT ID", "EVENTS", "USERS", "LAST SEEN", "FIRST SEEN", "TITLE"])
    if more:
        note(f"Showing {len(page)} issues; more are available. Next page: add -c next")


def event_json(state: dict, issue: dict, ev: dict, full: bool) -> dict:
    proj = next(p for p in state["projects"] if p["slug"] == issue["project"])
    tags = [{"key": "environment", "value": ev["environment"]}, {"key": "release", "value": ev["release"]},
            *({"key": k, "value": v} for k, v in ev.get("tags", {}).items())]
    top = ev["frames"][-1]
    out = {
        "id": ev["eventID"],
        "event.type": "error",
        "groupID": issue["id"],
        "eventID": ev["eventID"],
        "projectID": proj["id"],
        "message": f"{ev['type']}: {ev['value']}",
        "title": issue["title"],
        "location": f"{top['filename']}:{top['lineNo']}",
        "culprit": issue["culprit"],
        "user": ev.get("user"),
        "tags": tags,
        "platform": proj["platform"],
        "dateCreated": iso(ev["ago"]),
        "crashFile": None,
        "metadata": issue.get("metadata", {}),
    }
    if full:
        out["release"] = {"version": ev["release"]}
        out["environment"] = ev["environment"]
        out["entries"] = [{"type": "exception", "data": {"values": [{
            "type": ev["type"], "value": ev["value"], "mechanism": {"type": "generic", "handled": False},
            "stacktrace": {"frames": [{"filename": f["filename"], "absPath": f"/srv/app/{f['filename']}",
                                       "function": f["function"], "module": f.get("module"), "lineNo": f["lineNo"],
                                       "inApp": f.get("inApp", True), "context": [[f["lineNo"], f["line"]]],
                                       "vars": f.get("vars", {})} for f in ev["frames"]]},
        }]}}]
        out["contexts"] = ev.get("contexts", {})
        out["request"] = ev.get("request")
    return out


def print_event(issue: dict, ev: dict) -> None:
    print(f"Event {ev['eventID']}  ({humanize(ev['ago'])}, {iso(ev['ago'])})")
    print(f"  environment: {ev['environment']}   release: {ev['release']}")
    for k, v in ev.get("tags", {}).items():
        print(f"  {k}: {v}")
    if ev.get("request"):
        print(f"  request: {ev['request'].get('method', '')} {ev['request'].get('url', '')}")
    print(f"\n  {ev['type']}: {ev['value']}\n\n  Stack trace (most recent call last):")
    for f in ev["frames"]:
        print(f'    File "{f["filename"]}", line {f["lineNo"]}, in {f["function"]}' + ("" if f.get("inApp", True) else "  [library]"))
        print(f"      {f['line']}")
        for name, val in f.get("vars", {}).items():
            print(f"        {name} = {val}")


def issue_events(state: dict, issue: dict, opts: dict) -> list[dict]:
    start, end = period_window(opts["period"])
    evs = [e for e in issue["events"] if start <= at(e["ago"]) <= end]
    if opts.get("query"):
        q = opts["query"]
        for neg, key, val, quoted, word in QTOKEN.findall(q):
            vals = lambda e: {"environment": [e["environment"]], "release": [e["release"]], **{k: [v] for k, v in e.get("tags", {}).items()}}  # noqa: E731
            if key:
                evs = [e for e in evs if _match_value(val, vals(e).get(key, [])) != bool(neg)]
            else:
                evs = [e for e in evs if (quoted or word).lower() in f"{e['type']} {e['value']}".lower()]
    return sorted(evs, key=lambda e: e["ago"])


def cmd_issue_events(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <issue>")
    issue = find_issue(state, pos[0])
    evs = issue_events(state, issue, opts)
    limit = parse_limit(opts["limit"])
    key = json.dumps(["events", issue["id"], opts.get("query"), opts["period"], limit])
    page, more = paginate(state, key, evs, limit, opts.get("cursor"))
    full = bool(opts.get("full"))
    if wants_json(opts):
        emit_json([event_json(state, issue, e, full) for e in page], opts)
    elif not page:
        print(f"No events for {issue['shortId']} in the last {opts['period']}.")
    elif full:
        for e in page:
            print_event(issue, e)
            print()
    else:
        rows = [[e["eventID"], humanize(e["ago"]), e["environment"], e["release"],
                 f"{e['frames'][-1]['filename']}:{e['frames'][-1]['lineNo']}"] for e in page]
        table(rows, ["EVENT ID", "WHEN", "ENVIRONMENT", "RELEASE", "LOCATION"])
    if more:
        note("More events available. Next page: add -c next")


def cmd_issue_view(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <issue>")
    issue = find_issue(state, pos[0])
    data = issue_json(state, issue)
    if opts.get("web"):
        print(f"Opening {data['permalink']} in your browser...")
        return
    latest = min(issue["events"], key=lambda e: e["ago"]) if issue["events"] else None
    if wants_json(opts):
        data["tags"] = [{"key": k, "topValues": [{"value": v, "count": c} for v, c in vals.items()]}
                        for k, vals in issue.get("tags", {}).items()]
        data["event"] = event_json(state, issue, latest, True) if latest else None
        emit_json(data, opts)
        return
    print(f"{issue['shortId']}: {issue['title']}\n")
    status = issue["status"] + (f" (in release {issue['statusDetails']['inRelease']})" if issue.get("statusDetails", {}).get("inRelease") else "")
    print(f"  Status:     {status}    Level: {issue['level']}    Priority: {issue.get('priority', 'medium')}")
    print(f"  Project:    {data['project']['slug']}    Platform: {data['platform']}")
    print(f"  Events:     {int(issue['count']):,}    Users: {issue['userCount']:,}")
    print(f"  First seen: {data['firstSeen']} ({humanize(issue['firstSeenAgo'])})")
    print(f"  Last seen:  {data['lastSeen']} ({humanize(issue['lastSeenAgo'])})")
    print(f"  Culprit:    {issue['culprit']}")
    for k, vals in issue.get("tags", {}).items():
        print(f"  {k + ':':<11} " + ", ".join(f"{v} ({c:,})" for v, c in vals.items()))
    print(f"  Link:       {data['permalink']}\n")
    if latest:
        print("Latest event")
        print_event(issue, latest)


def _release_exists(state: dict, org: str, version: str) -> bool:
    return any(r["org"] == org and r["version"] == version for r in state["releases"])


def _mutate(state: dict, issue: dict, change: dict) -> None:
    before = {"status": issue["status"], "statusDetails": issue.get("statusDetails", {})}
    issue.update(change)
    state.setdefault("mutations", []).append({"issue": issue["shortId"], "before": before, "after": change})
    RECORD.setdefault("mutations", []).append({"issue": issue["shortId"], **change})
    save(state)


def resolve_status_details(state: dict, issue: dict, spec: str | None) -> dict:
    org = next(p for p in state["projects"] if p["slug"] == issue["project"])["org"]
    if not spec:
        return {}
    if spec == "@next":
        return {"inNextRelease": True}
    if spec == "@commit":
        raise CliError("Could not resolve @commit: no Sentry repository matches this checkout's `origin` remote. "
                       "Use --in @commit:<repo>@<sha> with a repository registered in Sentry, or resolve in a release.", 50)
    if spec.startswith("@commit:"):
        raise CliError(f"Unknown repository in {spec}: no repositories are registered for organization '{org}' (400).", 30)
    if spec.startswith("@"):
        raise input_error(f'Invalid --in value "{spec}". Use <version>, @next, @commit or @commit:<repo>@<sha>.')
    if not _release_exists(state, org, spec):
        raise CliError(f'Unable to find the given release: "{spec}" (400).', 30)
    return {"inRelease": spec}


def cmd_issue_resolve(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <issue>")
    issue = find_issue(state, pos[0])
    details = resolve_status_details(state, issue, opts.get("in"))
    _mutate(state, issue, {"status": "resolved", "statusDetails": details, "substatus": None})
    where = f" in release {details['inRelease']}" if "inRelease" in details else (
        " in the next release" if details else "")
    if wants_json(opts):
        emit_json(issue_json(state, issue), opts)
    else:
        print(f"Resolved {issue['shortId']}{where}.")


def cmd_issue_unresolve(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <issue>")
    issue = find_issue(state, pos[0])
    _mutate(state, issue, {"status": "unresolved", "statusDetails": {}, "substatus": "ongoing"})
    print(f"Reopened {issue['shortId']}.")


def cmd_issue_archive(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <issue>")
    issue = find_issue(state, pos[0])
    until = opts.get("until", "forever")
    _mutate(state, issue, {"status": "ignored", "statusDetails": {} if until == "forever" else {"until": until},
                           "substatus": "archived_forever" if until == "forever" else "archived_until_condition_met"})
    print(f"Archived {issue['shortId']}" + ("" if until == "forever" else f" until {until}") + ".")


def cmd_issue_merge(state, opts, pos):
    if len(pos) < 2:
        raise input_error("Merging requires at least 2 issues.")
    issues = [find_issue(state, p) for p in pos]
    parent = find_issue(state, opts["into"]) if opts.get("into") else max(issues, key=lambda i: int(i["count"]))
    for i in issues:
        if i is not parent:
            _mutate(state, i, {"merged_into": parent["shortId"]})
    print(f"Merged {len(issues) - 1} issue(s) into {parent['shortId']}.")


def cmd_issue_seer(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <issue>")
    find_issue(state, pos[0])
    raise CliError("Seer is not enabled for this organization. An org owner can enable it under Settings > Seer.", 40)


# ---------------------------------------------------------------- events


def cmd_event_view(state, opts, pos):
    if not pos:
        raise input_error("Expected at least 1 argument: <org/project/event-id...>")
    out = []
    for ref in pos:
        eid = ref.split("/")[-1].replace("-", "").lower()
        hit = next(((i, e) for i in state["issues"] for e in i["events"] if e["eventID"] == eid), None)
        if not hit:
            raise CliError(f"Event '{ref}' not found (404).", 30)
        RECORD.setdefault("issues", []).append(hit[0]["shortId"])
        out.append(hit)
    if wants_json(opts):
        objs = [event_json(state, i, e, True) for i, e in out]
        emit_json(objs[0] if len(objs) == 1 else objs, opts)
        return
    for i, e in out:
        print(f"{i['shortId']}: {i['title']}")
        print_event(i, e)
        print()


# ---------------------------------------------------------------- orgs, projects, releases


def cmd_org_list(state, opts, pos):
    orgs = state["orgs"][: parse_limit(opts["limit"])]
    if wants_json(opts):
        emit_json([{"id": o["id"], "slug": o["slug"], "name": o["name"]} for o in orgs], opts)
    else:
        table([[o["slug"], o["name"]] for o in orgs], ["SLUG", "NAME"])


def cmd_org_view(state, opts, pos):
    org = find_org(state, pos[0] if pos else (_detect(state) or ({"org": state["orgs"][0]["slug"]}, ""))[0]["org"])
    if wants_json(opts):
        emit_json({"id": org["id"], "slug": org["slug"], "name": org["name"]}, opts)
    else:
        print(f"{org['name']} ({org['slug']})\n  Projects: " + ", ".join(p["slug"] for p in state["projects"] if p["org"] == org["slug"]))


def project_json(p: dict) -> dict:
    return {"id": p["id"], "slug": p["slug"], "name": p["slug"], "platform": p["platform"],
            "organization": {"slug": p["org"]}, "dateCreated": iso(p.get("createdAgo", 400 * 86400))}


def cmd_project_list(state, opts, pos):
    projs = state["projects"]
    if pos:
        org, _, proj = pos[0].partition("/")
        find_org(state, org)
        projs = [p for p in projs if p["org"] == org and (not proj or p["slug"] == proj)]
    if opts.get("platform"):
        projs = [p for p in projs if p["platform"].startswith(opts["platform"])]
    projs = projs[: parse_limit(opts["limit"])]
    if wants_json(opts):
        emit_json([project_json(p) for p in projs], opts)
    else:
        table([[p["org"], p["slug"], p["platform"]] for p in projs], ["ORG", "PROJECT", "PLATFORM"])


def cmd_project_view(state, opts, pos):
    proj = resolve_projects(state, pos[0] if pos else None)[0]
    if wants_json(opts):
        emit_json(project_json(proj), opts)
    else:
        print(f"{proj['org']}/{proj['slug']}\n  Platform: {proj['platform']}\n  ID: {proj['id']}")


def cmd_project_delete(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <org/project>")
    proj = resolve_projects(state, pos[0])[0]
    if opts.get("dry-run"):
        print(f"Would delete project {proj['org']}/{proj['slug']}.")
        return
    if not (opts.get("yes") or opts.get("force")):
        raise CliError("Refusing to delete without confirmation in a non-interactive shell. Pass --yes to confirm.", 50)
    state["projects"].remove(proj)
    state.setdefault("mutations", []).append({"deleted_project": proj["slug"]})
    RECORD.setdefault("mutations", []).append({"deleted_project": proj["slug"]})
    save(state)
    print(f"Deleted project {proj['org']}/{proj['slug']}.")


def _split_org_version(state: dict, ref: str) -> tuple[str, str]:
    head, sep, rest = ref.partition("/")
    if sep and any(o["slug"] == head for o in state["orgs"]):
        return head, rest
    found = _detect(state)
    return (found[0]["org"] if found else state["orgs"][0]["slug"]), ref


def release_json(r: dict) -> dict:
    return {"version": r["version"], "shortVersion": r["version"].split("@")[-1], "dateCreated": iso(r["ago"]),
            "dateReleased": iso(r["ago"]), "projects": [{"slug": s} for s in r["projects"]],
            "lastDeploy": ({"environment": r["deploys"][-1]["environment"], "dateFinished": iso(r["deploys"][-1]["ago"])}
                           if r["deploys"] else None),
            "newGroups": r.get("newGroups", 0), "commitCount": r.get("commitCount", 0)}


def cmd_release_list(state, opts, pos):
    projs = resolve_projects(state, pos[0] if pos else None)
    slugs = {p["slug"] for p in projs}
    rels = sorted((r for r in state["releases"] if slugs & set(r["projects"])), key=lambda r: r["ago"])
    if opts.get("environment"):
        envs = {e for v in opts["environment"] for e in v.split(",")}
        rels = [r for r in rels if envs & {d["environment"] for d in r["deploys"]}]
    rels = rels[: parse_limit(opts["limit"])]
    if wants_json(opts):
        emit_json([release_json(r) for r in rels], opts)
    else:
        rows = [[r["version"], humanize(r["ago"]), ", ".join(f"{d['environment']} ({humanize(d['ago'])})" for d in r["deploys"]) or "-",
                 str(r.get("newGroups", 0))] for r in rels]
        table(rows, ["VERSION", "CREATED", "DEPLOYS", "NEW ISSUES"])


def cmd_release_view(state, opts, pos):
    if not pos:
        raise input_error("Expected at least 1 argument: <org/version...>")
    org, version = _split_org_version(state, pos[0])
    r = next((r for r in state["releases"] if r["org"] == org and r["version"] == version), None)
    if not r:
        raise CliError(f"Release '{version}' not found in organization '{org}' (404).", 30)
    if wants_json(opts):
        emit_json(release_json(r), opts)
    else:
        j = release_json(r)
        print(f"{r['version']}\n  Created: {j['dateCreated']}\n  Projects: {', '.join(r['projects'])}")
        for d in r["deploys"]:
            print(f"  Deployed to {d['environment']} {humanize(d['ago'])}")


def cmd_release_deploys(state, opts, pos):
    org, version = _split_org_version(state, pos[0]) if pos else (None, None)
    r = next((r for r in state["releases"] if r["org"] == org and r["version"] == version), None)
    if not r:
        raise CliError(f"Release '{version}' not found (404).", 30)
    rows = [[d["environment"], iso(d["ago"])] for d in r["deploys"]]
    if wants_json(opts):
        emit_json([{"environment": e, "dateFinished": t} for e, t in rows], opts)
    else:
        table(rows, ["ENVIRONMENT", "FINISHED"])


# ---------------------------------------------------------------- auth & misc


def cmd_auth(state, opts, pos, verb):
    user = state["user"]
    if verb == "status":
        print(f"Authenticated as {user['email']} (sentry.io)\n  Token: sntrys_****{state['token'][-4:]}\n  Organizations: "
              + ", ".join(o["slug"] for o in state["orgs"]))
    elif verb == "whoami":
        if wants_json(opts):
            emit_json({"email": user["email"], "name": user["name"]}, opts)
        else:
            print(f"{user['name']} <{user['email']}>")
    elif verb == "token":
        print(state["token"])
    elif verb == "login":
        print(f"Already logged in as {user['email']}. Use --force to re-authenticate.")
    elif verb == "logout":
        state["authenticated"] = False
        save(state)
        print("Logged out.")
    elif verb == "refresh":
        print("Token is still valid.")


def cmd_schema(state, opts, pos):
    endpoints = [
        ("GET", "/api/0/organizations/{organization_id_or_slug}/issues/", "List an organization's issues"),
        ("GET", "/api/0/projects/{organization_id_or_slug}/{project_id_or_slug}/issues/", "List a project's issues"),
        ("GET", "/api/0/organizations/{organization_id_or_slug}/issues/{issue_id}/", "Retrieve an issue"),
        ("PUT", "/api/0/organizations/{organization_id_or_slug}/issues/{issue_id}/", "Update an issue"),
        ("GET", "/api/0/organizations/{organization_id_or_slug}/issues/{issue_id}/events/", "List an issue's events"),
        ("GET", "/api/0/organizations/{organization_id_or_slug}/releases/", "List an organization's releases"),
        ("GET", "/api/0/organizations/", "List your organizations"),
    ]
    term = " ".join(pos) + " " + (opts.get("search") or "")
    hits = [e for e in endpoints if all(t.lower() in " ".join(e).lower() for t in term.split())]
    for m, p, d in hits or endpoints:
        print(f"{m:<6} {p}\n       {d}")


def cmd_api(state, opts, pos):
    if len(pos) != 1:
        raise input_error("Expected exactly 1 argument: <endpoint>")
    method = opts.get("method", "GET").upper()
    endpoint, _, qs = pos[0].partition("?")
    path = re.sub(r"^/?(api/0/)?", "", endpoint).strip("/")
    params = dict(p.split("=", 1) for p in qs.split("&") if "=" in p)
    body: dict = {}
    for raw, typed in [(f, True) for f in opts.get("field", [])] + [(f, False) for f in opts.get("raw-field", [])]:
        k, _, v = raw.partition("=")
        if typed:
            try:
                v = json.loads(v)
            except ValueError:
                pass
        m = re.match(r"^(\w+)\[(\w+)\]$", k)
        if m:
            body.setdefault(m.group(1), {})[m.group(2)] = v
        else:
            body[k] = v
    if opts.get("data"):
        body.update(json.loads(opts["data"]))
    if opts.get("input"):
        body.update(json.loads(sys.stdin.read() if opts["input"] == "-" else Path(opts["input"]).read_text()))
    if method == "GET":
        params.update({k: str(v) for k, v in body.items()})
    RECORD["api"] = {"method": method, "path": path, "params": params, "body": body}
    if opts.get("dry-run"):
        print(f"{method} https://sentry.io/api/0/{path}/" + (f"\n{json.dumps(body)}" if body else ""))
        return
    result = api_route(state, method, path.split("/"), params, body)
    if not opts.get("silent"):
        print(json.dumps(select_fields(result, opts.get("fields")), indent=2))


def api_route(state, method, parts, params, body):
    def issues_for(projs):
        return [issue_json(state, i) for i in query_issues(state, projs, params.get("query", "is:unresolved"),
                                                           params.get("sort", "date"), params.get("statsPeriod", "14d"))
                ][: int(params.get("limit", 100))]

    if parts == ["organizations"] and method == "GET":
        return [{"id": o["id"], "slug": o["slug"], "name": o["name"]} for o in state["orgs"]]
    if len(parts) == 2 and parts[0] == "organizations" and method == "GET":
        o = find_org(state, parts[1])
        return {"id": o["id"], "slug": o["slug"], "name": o["name"]}
    if len(parts) == 3 and parts[0] == "organizations" and parts[2] == "projects" and method == "GET":
        return [project_json(p) for p in state["projects"] if p["org"] == parts[1]]
    if len(parts) == 3 and parts[0] == "organizations" and parts[2] == "issues" and method == "GET":
        find_org(state, parts[1])
        projs = [p for p in state["projects"] if p["org"] == parts[1]
                 and (not params.get("project") or p["id"] == params["project"] or p["slug"] == params["project"])]
        RECORD["resolved"] = sorted(f"{p['org']}/{p['slug']}" for p in projs)
        return issues_for(projs)
    if len(parts) == 4 and parts[0] == "projects" and parts[3] == "issues" and method == "GET":
        projs = [find_project(state, parts[1], parts[2])]
        RECORD["resolved"] = [f"{parts[1]}/{parts[2]}"]
        return issues_for(projs)
    if parts[0] == "organizations" and len(parts) >= 4 and parts[2] == "issues":
        parts = parts[2:]
    if len(parts) >= 3 and parts[0] == "organizations" and parts[2] == "releases" and method == "GET":
        return [release_json(r) for r in state["releases"] if r["org"] == parts[1]]
    if len(parts) >= 4 and parts[0] == "projects" and parts[3] == "releases" and method == "GET":
        return [release_json(r) for r in state["releases"] if parts[2] in r["projects"]]
    if parts[0] == "issues" and len(parts) >= 2:
        issue = find_issue(state, parts[1])
        if len(parts) == 2 and method == "GET":
            return issue_json(state, issue)
        if len(parts) == 2 and method == "PUT":
            change = {}
            if "status" in body:
                if body["status"] not in ("resolved", "unresolved", "ignored", "resolvedInNextRelease"):
                    raise CliError(f'{{"status": ["\\"{body["status"]}\\" is not a valid choice."]}} (400)', 30)
                details = body.get("statusDetails") or {}
                if body["status"] == "resolvedInNextRelease":
                    change = {"status": "resolved", "statusDetails": {"inNextRelease": True}}
                elif body["status"] == "resolved" and details.get("inRelease"):
                    change = {"status": "resolved", "statusDetails": resolve_status_details(state, issue, details["inRelease"])}
                elif body["status"] == "resolved" and details.get("inNextRelease"):
                    change = {"status": "resolved", "statusDetails": {"inNextRelease": True}}
                else:
                    change = {"status": body["status"], "statusDetails": {}}
            if "assignedTo" in body:
                change["assignedTo"] = body["assignedTo"]
            if change:
                _mutate(state, issue, change)
            return issue_json(state, issue)
        if len(parts) == 2 and method == "DELETE":
            state["issues"].remove(issue)
            _mutate(state, issue, {"deleted": True})
            return {}
        if len(parts) >= 3 and parts[2] == "events" and method == "GET":
            evs = sorted(issue["events"], key=lambda e: e["ago"])
            if len(parts) == 4:
                if parts[3] in ("latest", "recommended"):
                    return event_json(state, issue, evs[0], True)
                ev = next((e for e in evs if e["eventID"] == parts[3]), None)
                if ev:
                    return event_json(state, issue, ev, True)
            else:
                return [event_json(state, issue, e, params.get("full") in ("true", "1")) for e in evs]
    raise CliError('{"detail": "The requested resource does not exist"} (404)', 30)


def cmd_empty(state, opts, pos, path):
    verb = path.split(" ")[-1]
    if verb in ("list", "revisions", "deploys", "logs"):
        if wants_json(opts):
            print("[]")
        else:
            print("No results found.")
        return
    if verb == "view":
        raise CliError(f"Not found: {' '.join(pos) or '(no target)'} (404).", 30)
    raise CliError(f"`sentry {path}` failed: the request could not be completed (503 Service Unavailable).", 50)


HANDLERS = {
    "issue list": cmd_issue_list,
    "issue view": cmd_issue_view,
    "issue events": cmd_issue_events,
    "event list": cmd_issue_events,
    "event view": cmd_event_view,
    "issue resolve": cmd_issue_resolve,
    "issue unresolve": cmd_issue_unresolve,
    "issue archive": cmd_issue_archive,
    "issue merge": cmd_issue_merge,
    "issue explain": cmd_issue_seer,
    "issue plan": cmd_issue_seer,
    "org list": cmd_org_list,
    "org view": cmd_org_view,
    "project list": cmd_project_list,
    "project view": cmd_project_view,
    "project delete": cmd_project_delete,
    "release list": cmd_release_list,
    "release view": cmd_release_view,
    "release deploys": cmd_release_deploys,
    "schema": cmd_schema,
    "api": cmd_api,
}


def run(argv: list[str]) -> int:
    if argv[:1] in (["--version"], ["-V"]):
        print(f"sentry {VERSION}")
        return 0
    path, rest = resolve_command(argv)
    RECORD["command"] = path
    if path not in SPEC:
        print_help(path)
        return 0
    opts, pos = parse_flags(path, rest)
    if opts.get("help"):
        print_help(path)
        return 0
    if opts.get("log-level") and opts["log-level"] not in ("error", "warn", "log", "info", "debug", "trace"):
        raise input_error(f'Invalid log level "{opts["log-level"]}"')
    state = load()
    if not state.get("authenticated", True) and path not in ("auth login", "auth status"):
        raise CliError("Not authenticated. Run `sentry auth login` to log in.", 10)
    if path.startswith("auth "):
        if path == "auth login":
            state["authenticated"] = True
            save(state)
        cmd_auth(state, opts, pos, path.split(" ")[1])
    elif path in HANDLERS:
        HANDLERS[path](state, opts, pos)
    else:
        cmd_empty(state, opts, pos, path)
    return 0


def main() -> int:
    argv = sys.argv[1:]
    try:
        code = run(argv)
    except CliError as e:
        print(f"Error: {e}", file=sys.stderr)
        code = e.code
    except BrokenPipeError:
        code = 0
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps({"at": NOW.isoformat(), "cwd": os.getcwd(), "argv": argv, "exit": code, **RECORD}) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())

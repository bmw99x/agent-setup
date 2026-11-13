#!/usr/bin/env python3
"""Offline stand-ins for `glab` and `gh`, serving the CI state of one merge/pull request.

Installed under both names; behaviour depends on the name it is invoked as. State lives in
/var/lib/fakes/state.json (written by seed.py). Every invocation is appended to
/var/log/fakes/calls.jsonl. Job retries / reruns are appended to state["retries"] and flip the
job to pending (GitLab: a new job id; GitHub: a new run attempt). Forge-side rebases, branch
updates and new pipelines are only logged, never performed.
"""

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote

STATE = Path("/var/lib/fakes/state.json")
LOG = Path("/var/log/fakes/calls.jsonl")
NOW = "2026-11-12T10:00:00Z"


def _load() -> dict:
    return json.loads(STATE.read_text())


def _save(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2))


def _log(tool: str, argv: list[str], **extra) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"at": datetime.now(UTC).isoformat(), "tool": tool, "cwd": os.getcwd(), "argv": argv, **extra}
    with LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def _git(state: dict, *args: str) -> str:
    out = subprocess.run(["git", f"--git-dir={state['bare']}", *args], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def _branch_sha(state: dict, branch: str) -> str:
    return _git(state, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")


def _diff(state: dict, base: str, head: str, name_only: bool = False) -> str:
    mb = _git(state, "merge-base", f"refs/heads/{base}", f"refs/heads/{head}")
    args = ["diff", "--no-color", mb, f"refs/heads/{head}"]
    if name_only:
        args.insert(1, "--name-only")
    return _git(state, *args)


def _emit(data, jq: str | None = None) -> None:
    text = json.dumps(data, indent=2)
    if jq:
        out = subprocess.run(["jq", "-r", jq], input=text, capture_output=True, text=True)
        sys.stdout.write(out.stdout)
        if out.returncode:
            sys.stderr.write(out.stderr)
            sys.exit(out.returncode)
    else:
        print(text)


def _opt(argv: list[str], *names: str) -> str | None:
    for i, a in enumerate(argv):
        for n in names:
            if a == n and i + 1 < len(argv):
                return argv[i + 1]
            if n.startswith("--") and a.startswith(n + "="):
                return a.split("=", 1)[1]
    return None


def _positionals(argv: list[str], with_value: set[str]) -> list[str]:
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a.startswith("-"):
            if a in with_value:
                skip = True
            continue
        out.append(a)
    return out


# ============================== GitLab ======================================


def _gl_job(state: dict, job: dict) -> dict:
    pipe = next(p for p in state["pipelines"] if p["id"] == job["pipeline_id"])
    data = {k: v for k, v in job.items() if k not in ("trace", "pipeline_id")}
    data["pipeline"] = {"id": pipe["id"], "ref": pipe["ref"], "sha": pipe["sha"], "status": pipe["status"]}
    data["ref"] = pipe["ref"]
    data["commit"] = {"id": pipe["sha"], "short_id": pipe["sha"][:8]}
    data["web_url"] = f"{state['web']}/-/jobs/{job['id']}"
    return data


def _gl_pipeline(state: dict, pipe: dict) -> dict:
    data = {k: v for k, v in pipe.items() if k != "jobs"}
    data["web_url"] = f"{state['web']}/-/pipelines/{pipe['id']}"
    return data


def _gl_jobs(state: dict, pid: int, include_retried: bool = False) -> list[dict]:
    pipe = _gl_find_pipeline(state, pid)
    jobs = [j for j in pipe["jobs"] if include_retried or not j["retried"]]
    return sorted(jobs, key=lambda j: -j["id"])


def _gl_find_pipeline(state: dict, pid: int) -> dict:
    pipe = next((p for p in state["pipelines"] if p["id"] == pid), None)
    if pipe is None:
        _gl_404(f"pipeline {pid}")
    return pipe


def _gl_all_jobs(state: dict) -> list[dict]:
    return [j for p in state["pipelines"] for j in p["jobs"]]


def _gl_404(what: str):
    print(json.dumps({"message": "404 Not Found"}))
    sys.exit(f"glab: 404 Not Found ({what})")


def _gl_mr(state: dict) -> dict:
    mr = dict(state["mr"])
    sha = _branch_sha(state, mr["source_branch"]) or mr["sha"]
    mr["sha"] = sha
    pipe = _gl_find_pipeline(state, mr.pop("head_pipeline_id"))
    mr["head_pipeline"] = _gl_pipeline(state, pipe)
    mr["pipeline"] = {k: mr["head_pipeline"][k] for k in ("id", "sha", "ref", "status", "web_url")}
    mr["web_url"] = f"{state['web']}/-/merge_requests/{mr['iid']}"
    mr["project_id"] = state["project_id"]
    return mr


def _gl_retry(state: dict, job: dict, via: str) -> dict:
    if job["retried"]:
        sys.exit(f"glab: 403 Forbidden - job {job['id']} has already been retried; retry the latest job instead")
    if job["status"] not in ("failed", "canceled", "success"):
        sys.exit(f"glab: 403 Forbidden - job {job['id']} is {job['status']} and cannot be retried")
    pipe = _gl_find_pipeline(state, job["pipeline_id"])
    job["retried"] = True
    new = {**job, "id": state["next_job_id"], "status": "pending", "retried": False, "trace": "",
           "duration": None, "started_at": None, "finished_at": None, "failure_reason": None,
           "created_at": NOW}
    state["next_job_id"] += 1
    pipe["jobs"].append(new)
    pipe["status"] = "running"
    state["retries"].append({"job_id": job["id"], "name": job["name"], "pipeline_id": pipe["id"],
                             "new_job_id": new["id"], "via": via})
    return new


def _gl_resolve_job(state: dict, ref: str, pid: int | None = None) -> dict:
    if ref.isdigit():
        job = next((j for j in _gl_all_jobs(state) if j["id"] == int(ref)), None)
    else:
        pid = pid or state["mr"]["head_pipeline_id"]
        job = next((j for j in _gl_jobs(state, pid) if j["name"] == ref), None)
    if job is None:
        _gl_404(f"job {ref}")
    return job


def _gl_api(argv: list[str]) -> None:
    state = _load()
    with_value = {"-X", "--method", "-F", "--field", "-f", "--raw-field", "-H", "--header", "--hostname", "--input"}
    pos = _positionals(argv, with_value)
    if not pos:
        sys.exit("glab api: endpoint argument required")
    method = (_opt(argv, "-X", "--method") or ("POST" if any(a in argv for a in ("-F", "-f", "--field", "--raw-field")) else "GET")).upper()
    raw = pos[0].lstrip("/")
    raw = re.sub(r"^api/v4/", "", raw)
    path, _, query = raw.partition("?")
    q = {k: v[-1] for k, v in parse_qs(query).items()}
    project = re.match(r"^projects/([^/]+)(/|$)(.*)$", path)
    _log("glab", argv, command="api", method=method, path=path)
    if path in ("user",):
        return _emit({"id": 7, "username": "dev"})
    if not project:
        _gl_404(path)
    pref = unquote(project.group(1))
    if pref not in (":id", str(state["project_id"]), state["repo"]):
        _gl_404(path)
    rest = project.group(3).rstrip("/")
    mr_iid = state["mr"]["iid"]

    if rest == "":
        return _emit({"id": state["project_id"], "path_with_namespace": state["repo"], "web_url": state["web"],
                      "default_branch": state["mr"]["target_branch"], **state.get("project", {})})
    if rest == "merge_requests":
        mr = _gl_mr(state)
        ok = (q.get("source_branch", mr["source_branch"]) == mr["source_branch"]
              and q.get("state", "opened") in ("opened", "all")
              and q.get("iids[]", str(mr_iid)) == str(mr_iid))
        return _emit([mr] if ok else [])
    m = re.match(r"^merge_requests/(\d+)(?:/(.*))?$", rest)
    if m:
        if int(m.group(1)) != mr_iid:
            _gl_404(path)
        sub = m.group(2) or ""
        mr = state["mr"]
        if sub == "":
            return _emit(_gl_mr(state))
        if sub == "pipelines":
            pipes = [p for p in state["pipelines"] if p["ref"].startswith(f"refs/merge-requests/{mr_iid}/")
                     or p["ref"] == mr["source_branch"]]
            return _emit([_gl_pipeline(state, p) for p in sorted(pipes, key=lambda p: -p["id"])])
        if sub in ("changes", "diffs"):
            text = _diff(state, mr["target_branch"], mr["source_branch"])
            files = [f for f in re.split(r"(?m)^diff --git ", text) if f.strip()]
            changes = []
            for f in files:
                head = f.splitlines()[0].split(" b/")
                changes.append({"old_path": head[0][2:], "new_path": head[-1], "diff": "\n".join(f.splitlines()[1:])})
            return _emit({**_gl_mr(state), "changes": changes} if sub == "changes" else changes)
        if sub == "commits":
            log = _git(state, "log", "--format=%H%x09%s", f"refs/heads/{mr['target_branch']}..refs/heads/{mr['source_branch']}")
            return _emit([{"id": ln.split("\t")[0], "short_id": ln[:8], "title": ln.split("\t", 1)[1]}
                          for ln in log.splitlines() if ln])
        if sub in ("notes", "discussions", "approvals", "approval_state"):
            if method != "GET":
                return _emit({"id": 1, "body": "posted"})
            return _emit({"approved": False, "approvals_left": 1} if sub.startswith("approval") else [])
        if sub == "rebase":
            return _emit({"rebase_in_progress": True})
        if sub == "merge":
            print(json.dumps({"message": "405 Method Not Allowed"}))
            sys.exit("glab: 405 Method Not Allowed - merge request is not mergeable")
        _gl_404(path)
    if rest == "pipelines":
        pipes = state["pipelines"]
        if "ref" in q:
            pipes = [p for p in pipes if p["ref"] == q["ref"]]
        if "sha" in q:
            pipes = [p for p in pipes if p["sha"].startswith(q["sha"])]
        if "status" in q:
            pipes = [p for p in pipes if p["status"] == q["status"]]
        return _emit([_gl_pipeline(state, p) for p in sorted(pipes, key=lambda p: -p["id"])])
    if rest == "pipeline" and method == "POST":
        return _emit({"id": 99999, "status": "created"})
    m = re.match(r"^pipelines/(\d+)(?:/(.*))?$", rest)
    if m:
        pid, sub = int(m.group(1)), m.group(2) or ""
        pipe = _gl_find_pipeline(state, pid)
        if sub == "":
            return _emit(_gl_pipeline(state, pipe))
        if sub == "jobs":
            jobs = _gl_jobs(state, pid, q.get("include_retried") == "true")
            scope = [v for k, vs in parse_qs(query).items() if k in ("scope", "scope[]") for v in vs]
            if scope:
                jobs = [j for j in jobs if j["status"] in scope]
            return _emit([_gl_job(state, j) for j in jobs])
        if sub == "bridges":
            return _emit([])
        if sub == "retry" and method == "POST":
            for j in [j for j in _gl_jobs(state, pid) if j["status"] in ("failed", "canceled")]:
                _gl_retry(state, j, via="pipeline retry")
            _save(state)
            return _emit(_gl_pipeline(state, pipe))
        _gl_404(path)
    m = re.match(r"^jobs/(\d+)(?:/(.*))?$", rest)
    if m:
        job = next((j for j in _gl_all_jobs(state) if j["id"] == int(m.group(1))), None)
        if job is None:
            _gl_404(path)
        sub = m.group(2) or ""
        if sub == "":
            return _emit(_gl_job(state, job))
        if sub == "trace":
            sys.stdout.write(job["trace"])
            return
        if sub == "retry" and method == "POST":
            new = _gl_retry(state, job, via="api")
            _save(state)
            return _emit(_gl_job(state, new))
        _gl_404(path)
    m = re.match(r"^repository/branches/(.+)$", rest)
    if m:
        name = unquote(m.group(1))
        sha = _branch_sha(state, name)
        if not sha:
            _gl_404(path)
        return _emit({"name": name, "commit": {"id": sha, "short_id": sha[:8]}})
    _gl_404(path)


def _gl_latest_pipeline(state: dict, argv: list[str]) -> dict:
    pid = _opt(argv, "-p", "--pipeline-id")
    if pid:
        return _gl_find_pipeline(state, int(pid))
    branch = _opt(argv, "-b", "--branch")
    if branch and branch != state["mr"]["source_branch"]:
        pipes = [p for p in state["pipelines"] if p["ref"] == branch]
        if not pipes:
            sys.exit(f"glab: no pipeline found for branch {branch}")
        return max(pipes, key=lambda p: p["id"])
    return _gl_find_pipeline(state, state["mr"]["head_pipeline_id"])


def glab(argv: list[str]) -> None:
    state = _load()
    two = argv[:2]
    if argv[:1] == ["api"]:
        return _gl_api(argv[1:])
    if two == ["mr", "view"]:
        _log("glab", argv, command="mr view")
        mr = _gl_mr(state)
        if _opt(argv, "-F", "--output") == "json":
            return _emit(mr)
        print(f"title:\t{mr['title']}\nstate:\topen\nauthor:\tdev\nnumber:\t{mr['iid']}\nsource:\t{mr['source_branch']}\n"
              f"target:\t{mr['target_branch']}\npipeline:\t#{mr['head_pipeline']['id']} {mr['head_pipeline']['status']}\n"
              f"merge status:\t{mr['detailed_merge_status']}\nurl:\t{mr['web_url']}\n--\n{mr['description']}")
        return
    if two == ["mr", "list"]:
        _log("glab", argv, command="mr list")
        mr = state["mr"]
        print(f"!{mr['iid']}\t{mr['title']}\t({mr['target_branch']}) ← ({mr['source_branch']})")
        return
    if two == ["mr", "diff"]:
        _log("glab", argv, command="mr diff")
        print(_diff(state, state["mr"]["target_branch"], state["mr"]["source_branch"]))
        return
    if two == ["mr", "rebase"]:
        _log("glab", argv, command="mr rebase")
        print("✓ Rebase successfully requested; the source branch will be rebased and force-pushed.")
        return
    if two == ["mr", "merge"]:
        _log("glab", argv, command="mr merge")
        sys.exit("glab: merge request is not mergeable")
    if two == ["ci", "status"]:
        _log("glab", argv, command="ci status")
        pipe = _gl_latest_pipeline(state, argv)
        for j in sorted(_gl_jobs(state, pipe["id"]), key=lambda j: j["id"]):
            flag = " (allowed to fail)" if j["allow_failure"] else ""
            print(f"({j['status']}) • {j['duration'] or '-'}s\t{j['stage']}\t{j['name']}{flag}")
        print(f"\nhttps://{state['host']}/{state['repo']}/-/pipelines/{pipe['id']}\nSHA: {pipe['sha']}\n"
              f"Pipeline state: {pipe['status']}")
        return
    if two == ["ci", "list"]:
        _log("glab", argv, command="ci list")
        pipes = sorted(state["pipelines"], key=lambda p: -p["id"])
        if _opt(argv, "-F", "--output") == "json":
            return _emit([_gl_pipeline(state, p) for p in pipes])
        for p in pipes:
            print(f"({p['status']}) • #{p['id']}\t{p['ref']}\t({p['created_at']})")
        return
    if two == ["ci", "get"]:
        _log("glab", argv, command="ci get")
        pipe = _gl_latest_pipeline(state, argv)
        data = {**_gl_pipeline(state, pipe), "jobs": [_gl_job(state, j) for j in _gl_jobs(state, pipe["id"])]}
        if _opt(argv, "-F", "--output") == "json":
            return _emit(data)
        print(f"# Pipeline:\nid:\t{pipe['id']}\nstatus:\t{pipe['status']}\nref:\t{pipe['ref']}\nsha:\t{pipe['sha']}\n\n# Jobs:")
        for j in sorted(_gl_jobs(state, pipe["id"]), key=lambda j: j["id"]):
            print(f"{j['name']}:\t{j['status']}" + ("\t(allowed to fail)" if j["allow_failure"] else "") + f"\tid={j['id']}")
        return
    if two in (["ci", "trace"], ["ci", "logs"]):
        _log("glab", argv, command="ci trace")
        pos = _positionals(argv[2:], {"-p", "--pipeline-id", "-b", "--branch", "-R", "--repo"})
        if not pos:
            sys.exit("glab: job id or name required in non-interactive mode")
        pid = _opt(argv, "-p", "--pipeline-id")
        sys.stdout.write(_gl_resolve_job(state, pos[0], int(pid) if pid else None)["trace"])
        return
    if two == ["ci", "retry"]:
        _log("glab", argv, command="ci retry")
        pos = _positionals(argv[2:], {"-p", "--pipeline-id", "-b", "--branch", "-R", "--repo"})
        if not pos:
            sys.exit("glab: job id or name required in non-interactive mode")
        pid = _opt(argv, "-p", "--pipeline-id")
        job = _gl_resolve_job(state, pos[0], int(pid) if pid else None)
        new = _gl_retry(state, job, via="glab ci retry")
        _save(state)
        print(f"Retried job (id: {new['id']}), status: pending, ref: {state['mr']['source_branch']}, "
              f"weburl: {state['web']}/-/jobs/{new['id']}")
        return
    if two == ["ci", "run"]:
        _log("glab", argv, command="ci run")
        print(f"Created pipeline (id: 99999), status: created, ref: {state['mr']['source_branch']}")
        return
    if two == ["ci", "view"]:
        _log("glab", argv, command="ci view")
        sys.exit("glab: interactive view is not available in this terminal; use `glab ci get` / `glab ci trace <job>`")
    if two == ["repo", "view"]:
        _log("glab", argv, command="repo view")
        print(f"name:\t{state['repo']}\nurl:\t{state['web']}\ndefault branch:\t{state['mr']['target_branch']}")
        return
    if two == ["auth", "status"]:
        _log("glab", argv, command="auth status")
        print(f"{state['host']}\n  ✓ Logged in to {state['host']} as dev")
        return
    _log("glab", argv, command="unsupported")
    sys.exit(f"glab: unsupported in this environment: {' '.join(argv)}")


# ============================== GitHub ======================================


def _gh_run(state: dict, run_id) -> dict:
    run = next((r for r in state["runs"] if str(r["databaseId"]) == str(run_id)), None)
    if run is None:
        sys.exit(f"gh: could not find any workflow run with ID {run_id}")
    return run


def _gh_latest_jobs(run: dict, attempt: int | None = None) -> list[dict]:
    attempt = attempt or run["attempt"]
    return [j for j in run["jobs"] if j["run_attempt"] == attempt]


def _gh_job(state: dict, job_id) -> tuple[dict, dict]:
    for run in state["runs"]:
        for j in run["jobs"]:
            if str(j["databaseId"]) == str(job_id):
                return run, j
    sys.exit(f"gh: HTTP 404: Not Found (job {job_id})")


def _gh_job_url(state: dict, run: dict, job: dict) -> str:
    return f"{state['web']}/actions/runs/{run['databaseId']}/job/{job['databaseId']}"


def _gh_job_json(state: dict, run: dict, job: dict) -> dict:
    data = {k: v for k, v in job.items() if k not in ("log", "steps_log")}
    data["url"] = _gh_job_url(state, run, job)
    return data


def _gh_checks(state: dict) -> list[dict]:
    pr = state["pr"]
    out = []
    for run in state["runs"]:
        if run["headSha"] != pr["headRefOid"]:
            continue
        for j in _gh_latest_jobs(run):
            bucket = {"success": "pass", "failure": "fail", "cancelled": "fail", "skipped": "skipping"}.get(
                j["conclusion"] or "", "pending")
            out.append({"name": j["name"], "state": (j["conclusion"] or j["status"]).upper(), "bucket": bucket,
                        "link": _gh_job_url(state, run, j), "workflow": run["workflowName"], "event": run["event"],
                        "startedAt": j.get("startedAt"), "completedAt": j.get("completedAt"),
                        "description": ""})
    return out


def _gh_pr(state: dict) -> dict:
    pr = dict(state["pr"])
    pr["headRefOid"] = _branch_sha(state, pr["headRefName"]) or pr["headRefOid"]
    pr["statusCheckRollup"] = [
        {"__typename": "CheckRun", "name": c["name"], "status": "COMPLETED" if c["bucket"] != "pending" else "IN_PROGRESS",
         "conclusion": c["state"] if c["bucket"] != "pending" else "", "detailsUrl": c["link"],
         "workflowName": c["workflow"]} for c in _gh_checks(state)]
    names = _diff(state, pr["baseRefName"], pr["headRefName"], name_only=True).splitlines()
    pr["files"] = [{"path": n} for n in names if n]
    return pr


def _gh_select(data: dict, argv: list[str]):
    fields = _opt(argv, "--json")
    if fields is None:
        return None
    keys = [f.strip() for f in fields.split(",") if f.strip()]
    if isinstance(data, list):
        return [{k: d.get(k) for k in keys} for d in data]
    return {k: data.get(k) for k in keys}


def _gh_rerun(state: dict, run: dict, jobs: list[dict], via: str) -> None:
    run["attempt"] += 1
    for j in _gh_latest_jobs(run, run["attempt"] - 1):
        rerun = j in jobs
        new = {**j, "run_attempt": run["attempt"]}
        if rerun:
            new.update(status="queued", conclusion=None, log="", startedAt=None, completedAt=None,
                       databaseId=state["next_job_id"])
            state["next_job_id"] += 1
            state["retries"].append({"job_id": j["databaseId"], "name": j["name"], "run_id": run["databaseId"],
                                     "new_job_id": new["databaseId"], "via": via})
        run["jobs"].append(new)
    run["status"], run["conclusion"] = "queued", None


def _gh_log(job: dict, failed_only: bool) -> str:
    lines = []
    for step in job["steps_log"]:
        if failed_only and step["conclusion"] != "failure":
            continue
        for ln in step["log"].splitlines():
            lines.append(f"{job['name']}\t{step['name']}\t{ln}")
    return "\n".join(lines) + "\n"


def _gh_api(argv: list[str]) -> None:
    state = _load()
    with_value = {"-X", "--method", "-F", "--field", "-f", "--raw-field", "-H", "--header", "--hostname",
                  "--input", "-q", "--jq", "-t", "--template", "--cache"}
    pos = _positionals(argv, with_value)
    method = (_opt(argv, "-X", "--method") or ("POST" if any(a in argv for a in ("-F", "-f", "--field", "--raw-field")) else "GET")).upper()
    jq = _opt(argv, "-q", "--jq")
    raw = (pos[0] if pos else "").lstrip("/").replace("{owner}/{repo}", state["repo"])
    path, _, query = raw.partition("?")
    q = {k: v[-1] for k, v in parse_qs(query).items()}
    _log("gh", argv, command="api", method=method, path=path)
    prefix = f"repos/{state['repo']}"
    if path == "user":
        return _emit({"login": "dev"}, jq)
    if not path.startswith(prefix):
        sys.exit(f"gh: HTTP 404: Not Found ({path})")
    rest = path[len(prefix):].strip("/")
    pr = _gh_pr(state)
    if rest == "":
        return _emit({"full_name": state["repo"], "default_branch": pr["baseRefName"], "html_url": state["web"],
                      "allow_merge_commit": True, "allow_squash_merge": True}, jq)
    m = re.match(r"^pulls/(\d+)(?:/(.*))?$", rest)
    if m:
        if int(m.group(1)) != pr["number"]:
            sys.exit(f"gh: HTTP 404: Not Found ({path})")
        sub = m.group(2) or ""
        if sub == "":
            base_sha = _branch_sha(state, pr["baseRefName"])
            return _emit({"number": pr["number"], "state": "open", "title": pr["title"], "body": pr["body"],
                          "html_url": pr["url"], "head": {"ref": pr["headRefName"], "sha": pr["headRefOid"]},
                          "base": {"ref": pr["baseRefName"], "sha": base_sha}, "mergeable": True,
                          "mergeable_state": pr["mergeStateStatus"].lower(), "draft": False}, jq)
        if sub == "files":
            return _emit([{"filename": f["path"], "status": "modified"} for f in pr["files"]], jq)
        if sub in ("comments", "reviews") or sub.startswith("reviews"):
            return _emit([], jq)
        if sub == "update-branch":
            return _emit({"message": "Updating pull request branch.", "url": pr["url"]}, jq)
        sys.exit(f"gh: HTTP 404: Not Found ({path})")
    m = re.match(r"^issues/(\d+)/comments$", rest)
    if m:
        return _emit([] if method == "GET" else {"id": 1}, jq)
    m = re.match(r"^commits/([0-9a-f]+)/(check-runs|status|check-suites)$", rest)
    if m:
        checks = _gh_checks(state) if pr["headRefOid"].startswith(m.group(1)) else []
        if m.group(2) == "status":
            return _emit({"state": "success" if not checks else "pending", "statuses": [], "total_count": 0}, jq)
        runs = [{"id": int(c["link"].rsplit("/", 1)[-1]), "name": c["name"], "status": "completed",
                 "conclusion": c["state"].lower(), "html_url": c["link"], "details_url": c["link"]} for c in checks]
        return _emit({"total_count": len(runs), "check_runs": runs}, jq)
    if rest == "actions/runs":
        runs = [r for r in state["runs"] if q.get("branch", r["headBranch"]) == r["headBranch"]]
        return _emit({"total_count": len(runs), "workflow_runs": [
            {"id": r["databaseId"], "name": r["workflowName"], "head_branch": r["headBranch"], "head_sha": r["headSha"],
             "status": r["status"], "conclusion": r["conclusion"], "run_attempt": r["attempt"], "event": r["event"],
             "html_url": f"{state['web']}/actions/runs/{r['databaseId']}"} for r in runs]}, jq)
    m = re.match(r"^actions/runs/(\d+)(?:/(.*))?$", rest)
    if m:
        run = _gh_run(state, m.group(1))
        sub = m.group(2) or ""
        if sub == "":
            return _emit({"id": run["databaseId"], "name": run["workflowName"], "head_branch": run["headBranch"],
                          "head_sha": run["headSha"], "status": run["status"], "conclusion": run["conclusion"],
                          "run_attempt": run["attempt"], "event": run["event"],
                          "html_url": f"{state['web']}/actions/runs/{run['databaseId']}"}, jq)
        am = re.match(r"^(?:attempts/(\d+)/)?jobs$", sub)
        if am:
            if am.group(1):
                jobs = _gh_latest_jobs(run, int(am.group(1)))
            elif q.get("filter") == "all":
                jobs = run["jobs"]
            else:
                jobs = _gh_latest_jobs(run)
            return _emit({"total_count": len(jobs), "jobs": [
                {"id": j["databaseId"], "name": j["name"], "status": j["status"], "conclusion": j["conclusion"],
                 "run_attempt": j["run_attempt"], "html_url": _gh_job_url(state, run, j), "steps": j["steps"]}
                for j in jobs]}, jq)
        if sub in ("rerun", "rerun-failed-jobs") and method == "POST":
            jobs = _gh_latest_jobs(run)
            if sub == "rerun-failed-jobs":
                jobs = [j for j in jobs if j["conclusion"] in ("failure", "cancelled")]
            _gh_rerun(state, run, jobs, via=f"api {sub}")
            _save(state)
            return
        sys.exit(f"gh: HTTP 404: Not Found ({path})")
    m = re.match(r"^actions/jobs/(\d+)(?:/(.*))?$", rest)
    if m:
        run, job = _gh_job(state, m.group(1))
        sub = m.group(2) or ""
        if sub == "":
            return _emit({"id": job["databaseId"], "run_id": run["databaseId"], "name": job["name"],
                          "status": job["status"], "conclusion": job["conclusion"], "run_attempt": job["run_attempt"],
                          "steps": job["steps"], "html_url": _gh_job_url(state, run, job)}, jq)
        if sub == "logs":
            sys.stdout.write("\n".join(s["log"] for s in job["steps_log"]) + "\n")
            return
        if sub == "rerun" and method == "POST":
            if job["run_attempt"] != run["attempt"]:
                sys.exit("gh: HTTP 403: job is not from the latest run attempt")
            _gh_rerun(state, run, [job], via="api job rerun")
            _save(state)
            return
    sys.exit(f"gh: HTTP 404: Not Found ({path})")


def gh(argv: list[str]) -> None:
    state = _load()
    two = argv[:2]
    jq = _opt(argv, "-q", "--jq")
    if argv[:1] == ["api"]:
        return _gh_api(argv[1:])
    if two == ["pr", "view"]:
        _log("gh", argv, command="pr view")
        pr = _gh_pr(state)
        sel = _gh_select(pr, argv)
        if sel is not None:
            return _emit(sel, jq)
        print(f"{pr['title']} #{pr['number']}\nOpen • dev wants to merge into {pr['baseRefName']} from "
              f"{pr['headRefName']}\n\n{pr['body']}\n\nView this pull request on GitHub: {pr['url']}")
        return
    if two == ["pr", "checks"]:
        _log("gh", argv, command="pr checks")
        checks = _gh_checks(state)
        sel = _gh_select(checks, argv)
        if sel is not None:
            _emit(sel, jq)
        else:
            for c in checks:
                print(f"{c['name']}\t{c['bucket']}\t\t{c['link']}")
        buckets = {c["bucket"] for c in checks}
        sys.exit(1 if "fail" in buckets else 8 if "pending" in buckets else 0)
    if two == ["pr", "diff"]:
        _log("gh", argv, command="pr diff")
        pr = state["pr"]
        print(_diff(state, pr["baseRefName"], pr["headRefName"], name_only="--name-only" in argv))
        return
    if two == ["pr", "list"]:
        _log("gh", argv, command="pr list")
        pr = state["pr"]
        print(f"#{pr['number']}\t{pr['title']}\t{pr['headRefName']}\tOPEN")
        return
    if two in (["pr", "update-branch"], ["pr", "merge"]):
        _log("gh", argv, command=" ".join(two))
        if two[1] == "merge":
            sys.exit("gh: Pull request is not mergeable: required status checks have not succeeded")
        print("✓ PR branch updated")
        return
    if two == ["run", "list"]:
        _log("gh", argv, command="run list")
        runs = [{"databaseId": r["databaseId"], "name": r["workflowName"], "workflowName": r["workflowName"],
                 "headBranch": r["headBranch"], "headSha": r["headSha"], "status": r["status"],
                 "conclusion": r["conclusion"], "event": r["event"], "attempt": r["attempt"],
                 "url": f"{state['web']}/actions/runs/{r['databaseId']}", "createdAt": r["createdAt"],
                 "displayTitle": r["displayTitle"]} for r in state["runs"]]
        branch = _opt(argv, "-b", "--branch")
        if branch:
            runs = [r for r in runs if r["headBranch"] == branch]
        sel = _gh_select(runs, argv)
        if sel is not None:
            return _emit(sel, jq)
        for r in runs:
            print(f"{r['conclusion'] or r['status']}\t{r['displayTitle']}\t{r['workflowName']}\t{r['headBranch']}\t"
                  f"{r['event']}\t{r['databaseId']}")
        return
    if two == ["run", "view"]:
        _log("gh", argv, command="run view")
        job_id = _opt(argv, "-j", "--job")
        pos = _positionals(argv[2:], {"-j", "--job", "--json", "-q", "--jq", "-a", "--attempt", "-t", "--template",
                                      "-R", "--repo"})
        if job_id:
            run, job = _gh_job(state, job_id)
        else:
            if not pos:
                sys.exit("gh: run or job ID required when not running interactively")
            run, job = _gh_run(state, pos[0]), None
        attempt = int(_opt(argv, "-a", "--attempt") or run["attempt"])
        if "--log" in argv or "--log-failed" in argv:
            failed = "--log-failed" in argv
            jobs = [job] if job else [j for j in _gh_latest_jobs(run, attempt) if not failed or j["conclusion"] == "failure"]
            for j in jobs:
                sys.stdout.write(_gh_log(j, failed))
            return
        data = {"databaseId": run["databaseId"], "attempt": attempt, "status": run["status"],
                "conclusion": run["conclusion"], "headSha": run["headSha"], "headBranch": run["headBranch"],
                "event": run["event"], "workflowName": run["workflowName"], "name": run["workflowName"],
                "displayTitle": run["displayTitle"], "url": f"{state['web']}/actions/runs/{run['databaseId']}",
                "jobs": [_gh_job_json(state, run, j) for j in _gh_latest_jobs(run, attempt)]}
        if job:
            data = {**data, **_gh_job_json(state, run, job)}
        sel = _gh_select(data, argv)
        if sel is not None:
            return _emit(sel, jq)
        print(f"{run['conclusion'] or run['status']} {run['headBranch']} {run['workflowName']} · {run['databaseId']}"
              f" (attempt #{attempt})\nTriggered via {run['event']}\n\nJOBS")
        for j in _gh_latest_jobs(run, attempt):
            print(f"{'X' if j['conclusion'] == 'failure' else '✓'} {j['name']} (ID {j['databaseId']})")
            if j["conclusion"] == "failure":
                for s in j["steps"]:
                    if s["conclusion"] == "failure":
                        print(f"  X {s['name']}")
        print(f"\nFor more information about a job, try: gh run view --job=<job-id>\n"
              f"View this run on GitHub: {state['web']}/actions/runs/{run['databaseId']}")
        return
    if two == ["run", "rerun"]:
        _log("gh", argv, command="run rerun")
        job_id = _opt(argv, "-j", "--job")
        pos = _positionals(argv[2:], {"-j", "--job", "-R", "--repo"})
        if job_id:
            run, job = _gh_job(state, job_id)
            if job["run_attempt"] != run["attempt"]:
                sys.exit("gh: job is not from the latest run attempt")
            jobs = [job]
        else:
            if not pos:
                sys.exit("gh: run or job ID required when not running interactively")
            run = _gh_run(state, pos[0])
            jobs = _gh_latest_jobs(run)
            if "--failed" in argv:
                jobs = [j for j in jobs if j["conclusion"] in ("failure", "cancelled")]
        _gh_rerun(state, run, jobs, via="gh run rerun")
        _save(state)
        print(f"✓ Requested rerun of run {run['databaseId']}")
        return
    if two == ["run", "watch"]:
        _log("gh", argv, command="run watch")
        sys.exit("gh: run watch is not available in this terminal")
    if two == ["repo", "view"]:
        _log("gh", argv, command="repo view")
        info = {"nameWithOwner": state["repo"], "url": state["web"], "defaultBranchRef": {"name": state["pr"]["baseRefName"]}}
        sel = _gh_select(info, argv)
        return _emit(sel if sel is not None else info, jq)
    if two == ["auth", "status"]:
        _log("gh", argv, command="auth status")
        print(f"{state['host']}\n  ✓ Logged in to {state['host']} account dev")
        return
    _log("gh", argv, command="unsupported")
    sys.exit(f"gh: unsupported in this environment: {' '.join(argv)}")


if __name__ == "__main__":
    {"glab": glab, "gh": gh}[Path(sys.argv[0]).name](sys.argv[1:])

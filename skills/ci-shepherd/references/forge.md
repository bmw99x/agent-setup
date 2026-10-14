# Forge commands — GitHub (`gh`) and GitLab (`glab`)

Detect the forge from `git remote get-url origin` (or which CLI is authenticated). `gh` filters with
`--jq`; `glab api` has no filter flag, so pipe to `jq`. `glab api` fills `:id` with the current
project. Trim with jq before output reaches context — never dump a full payload.

## Change request (PR / MR)

| Need | GitHub | GitLab |
|---|---|---|
| Resolve current | `gh pr view --json number,url,baseRefName,headRefOid,state --jq '{number,url,base:.baseRefName,head:.headRefOid,state}'` | `glab api "projects/:id/merge_requests?source_branch=$(git branch --show-current)&state=opened" \| jq '.[0] \| {iid,web_url,target_branch,sha,state}'` |
| View by number | `gh pr view <n> --json …` | `glab api projects/:id/merge_requests/<iid> \| jq '{…}'` |
| Diff to a file | `gh pr diff <n> > <scratch>/cr-<sha>.patch` | `glab mr diff <iid> --color never > <scratch>/cr-<sha>.patch` |

Take the diff from the forge, not a local base ref: in a worktree the local base is usually stale,
and a diff against it can balloon to the whole history.

## Merge state

| Meaning | GitHub `mergeStateStatus` / `mergeable` | GitLab `detailed_merge_status` |
|---|---|---|
| Behind, and the forge requires it current | `BEHIND` | `need_rebase` |
| Conflicts with base | `DIRTY` / `CONFLICTING` | `conflict` (`has_conflicts: true`) |
| Blocked by approvals or discussions — not a stale base | `BLOCKED` | `not_approved`, `discussions_not_resolved` |
| Fine | `CLEAN`, `UNSTABLE`, `HAS_HOOKS` | `mergeable`, `ci_must_pass`, `ci_still_running` |
| Not computed yet — re-read once | `UNKNOWN` | `unchecked`, `checking` |

GitHub: `gh pr view <n> --json mergeable,mergeStateStatus`. GitLab:
`glab api "projects/:id/merge_requests/<iid>?include_diverged_commits_count=true" | jq '{detailed_merge_status,has_conflicts,diverged_commits_count}'`.

Do not use `glab mr rebase`. It rewrites history and force-pushes.

## CI

| Need | GitHub | GitLab |
|---|---|---|
| Check summary | `gh pr checks <n> --json name,bucket,link --jq '…' \|\| true` (non-zero exit means pending/failing — signal, not error) | `glab api projects/:id/merge_requests/<iid> \| jq '.head_pipeline \| {id,status}'` then `glab api "projects/:id/pipelines/<pid>/jobs?per_page=100" \| jq '[.[] \| {id,name,stage,status,allow_failure}]'` |
| Failed leaf jobs | parse run/job IDs from failing `link`s | jobs with `status == "failed"` and `allow_failure == false` |
| Failed log | `gh run view --job <job_id> --log-failed` | `glab api projects/:id/jobs/<job_id>/trace` — trim to the failing step's tail |
| Attempt / retried? | `gh run view <run_id> --json attempt --jq .attempt` | `glab api "projects/:id/pipelines/<pid>/jobs?include_retried=true" \| jq` — more than one job with the same name means already retried |
| Rerun one job | `gh run rerun <run_id> --job <job_id>` | `glab ci retry <job_id>` |

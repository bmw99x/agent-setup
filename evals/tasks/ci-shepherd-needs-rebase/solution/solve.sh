#!/bin/bash
set -e; cd /app
glab api "projects/:id/merge_requests/77?include_diverged_commits_count=true" | jq '{detailed_merge_status,has_conflicts,diverged_commits_count}'
glab api "projects/:id/pipelines/5520/jobs" | jq -c '.[] | {id,name,status}'
glab api projects/:id/jobs/31101/trace | tail -14
sed -i '/normalised = word.strip/d' catalog/search.py
ruff check .
python -m pytest -q
git add catalog/search.py
git commit -q -m "fix(search): drop unused variable"
git push -q origin HEAD
cat > CI_REPORT.md <<'MD'
[ci] done — mr 77 base=behind repair=committed rerun=0 observed=pass=2 pending=0 fail=1 (pre-repair)

- ruff F841 (unused `normalised` in catalog/search.py): fixed in a new commit; `ruff check .`, `pytest -q`.
- The MR is 2 commits behind main and the project merges fast-forward only (need_rebase). Bringing
  main in means rebasing + force-pushing, or a merge commit — your call; I did neither.
MD

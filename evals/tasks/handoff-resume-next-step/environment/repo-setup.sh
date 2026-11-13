set -e
cd /app
mv wip /tmp/wip
git init -q
git checkout -q -b feature/csv-export
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add -A
GIT_AUTHOR_DATE="2026-11-11T16:50:00" GIT_COMMITTER_DATE="2026-11-11T16:50:00" \
  git commit -q -m "feat(export): header row; bump to 0.4.0"
cp /tmp/wip/test_export_quoting.py tests/test_export_quoting.py
git add tests/test_export_quoting.py
GIT_AUTHOR_DATE="2026-11-11T17:35:00" GIT_COMMITTER_DATE="2026-11-11T17:35:00" \
  git commit -q -m "test(export): failing tests for quoting awkward fields"
mkdir -p .claude/handoffs
cp /tmp/wip/handoff.md .claude/handoffs/2026-11-11-174200-csv-export-quoting.md
git add .claude
GIT_AUTHOR_DATE="2026-11-11T17:42:00" GIT_COMMITTER_DATE="2026-11-11T17:42:00" \
  git commit -q -m "chore: session handoff"
rm -rf /tmp/wip
sha256sum .claude/handoffs/2026-11-11-174200-csv-export-quoting.md > /etc/eval-handoff-sha
git rev-parse HEAD > /etc/eval-base-sha

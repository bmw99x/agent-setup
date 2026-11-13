#!/bin/bash
# Reference solution: fetch open threads, locate code by content (positions refer to an older head),
# fix, verify, push once, rebase the stacked MR with --force-with-lease, reply per thread, propose skill updates.
set -euo pipefail
cd /app
SCRATCH=$(mktemp -d)
glab api --paginate "projects/:id/merge_requests/64/discussions?per_page=100" | jq -r '
  .[] | select(.notes[0].resolvable == true and (.notes | map(select(.resolvable and (.resolved|not))) | length > 0))
  | "[\(.id)] \(.notes[0].position.new_path // "-"):\(.notes[0].position.new_line // "-") :: \(.notes[0].body | gsub("\n"; " "))"
' > "$SCRATCH/threads.txt"
cat "$SCRATCH/threads.txt"
tid() { grep -F "$1" "$SCRATCH/threads.txt" | sed -E 's/^\[([^]]+)\].*/\1/'; }
T_INCL=$(tid "exactly at its reorder level"); T_DISC=$(tid "Discontinued"); T_LOG=$(tid "CHANGELOG")

python3 - <<'PY'
from pathlib import Path
p = Path("stock/alerts.py"); s = p.read_text()
old = "    return [item for item in items if item.on_hand < item.reorder_level]"
assert old in s
s = s.replace(old, "    return [item for item in items if not item.discontinued and item.on_hand <= item.reorder_level]")
p.write_text(s)
t = Path("tests/test_alerts.py")
t.write_text(t.read_text() + '''

def test_item_at_its_reorder_level_is_flagged():
    assert [i.sku for i in low_stock([Item("SKU-1", 10, 10, COUNTED)])] == ["SKU-1"]


def test_discontinued_items_are_not_flagged():
    assert low_stock([Item("SKU-1", 0, 10, COUNTED, discontinued=True)]) == []
''')
c = Path("CHANGELOG.md")
c.write_text(c.read_text().replace("## Unreleased\n", "## Unreleased\n\n- Morning low-stock and cycle-count alerts for purchasing.\n"))
PY
ruff check .
python -m pytest -q
git add stock tests CHANGELOG.md
git commit -q -m "fix(alerts): flag items at their reorder level, skip discontinued items" -m "Adds the CHANGELOG entry."
FIX=$(git rev-parse --short HEAD)
git push -q origin HEAD

git checkout -q feature/low-stock-csv
git rebase -q feature/low-stock-alerts
python -m pytest -q
git push -q --force-with-lease origin feature/low-stock-csv
git checkout -q feature/low-stock-alerts

reply() { glab api -X POST "projects/:id/merge_requests/64/discussions/$1/notes" -f body="$2" >/dev/null; }
reply "$T_INCL" "Fixed in $FIX: \`low_stock\` now flags items at their reorder level (\`<=\`)."
reply "$T_DISC" "Fixed in $FIX: discontinued items are left out of \`low_stock\`."
reply "$T_LOG" "Added in $FIX under Unreleased."

cat > HANDOFF.md <<MD
# !64 review feedback

Three open threads fixed in $FIX, pushed, replied to; threads left for Dana and Raj to resolve.
!65 is rebased onto the updated !64 and pushed with --force-with-lease; its suite passes.
Note: the thread positions point at the commit before the cycle-count change, so line numbers are stale.

## Proposed skill updates

Nothing applied yet.

- repo / domain — stock conventions — reorder level is inclusive; discontinued items never alert — (threads: ${T_INCL:0:8}, ${T_DISC:0:8})
- repo / repo-specific convention — commit-flow — user-facing changes get a CHANGELOG entry under Unreleased — (threads: ${T_LOG:0:8})
MD

#!/bin/bash
# Reference solution: GraphQL for unresolved threads, fix two, decline one with a reason, verify,
# push once, reply on each thread, propose skill updates.
set -euo pipefail
cd /app
SCRATCH=$(mktemp -d)
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){
  reviewThreads(first:100){nodes{id isResolved path line comments(first:1){nodes{databaseId body}}}}}}}' \
  -f o=acme -f r=bookings -F n=31 | jq -r '
  .data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved|not)
  | "[\(.id)] \(.path):\(.line // "-") :: \(.comments.nodes[0].body | gsub("\n"; " "))"' > "$SCRATCH/threads.txt"
cat "$SCRATCH/threads.txt"
tid() { grep -F "$1" "$SCRATCH/threads.txt" | sed -E 's/^\[([^]]+)\].*/\1/'; }
T_ROUND=$(tid "ROUND_HALF_UP"); T_WINDOW=$(tid "48"); T_UTC=$(tid "utcnow")

python3 - <<'PY'
from pathlib import Path
p = Path("bookings/policy.py"); s = p.read_text()
s = s.replace("timedelta(hours=24)", "timedelta(hours=48)")
s = s.replace("CANCELLATION_FEE_RATE = 0.10", 'CANCELLATION_FEE_RATE = Decimal("0.10")')
s = s.replace("from datetime import timedelta\n", "from datetime import timedelta\nfrom decimal import Decimal\n")
p.write_text(s)
p = Path("bookings/fees.py"); s = p.read_text()
s = s.replace("from datetime import datetime\n", "from datetime import datetime\nfrom decimal import ROUND_HALF_UP, Decimal\n")
s = s.replace("    return round(booking.total_pence * CANCELLATION_FEE_RATE)",
              "    fee = Decimal(booking.total_pence) * CANCELLATION_FEE_RATE\n"
              "    return int(fee.quantize(Decimal(1), rounding=ROUND_HALF_UP))")
p.write_text(s)
t = Path("tests/test_cancel.py")
t.write_text(t.read_text() + '''

def test_fee_rounds_half_up():
    assert cancel_booking(Booking("B1", 125, CHECK_IN), CHECK_IN - timedelta(hours=3)).fee_pence == 13


def test_cancelling_inside_48_hours_is_charged():
    booking = Booking("B1", 20000, CHECK_IN)
    assert cancel_booking(booking, CHECK_IN - timedelta(hours=30)).fee_pence == 2000
''')
PY
ruff check .
python -m pytest -q
git add bookings tests
git commit -q -m "fix(cancellations): 48-hour free window and half-up fee rounding"
FIX=$(git rev-parse --short HEAD)
git push -q origin HEAD

reply() {
  gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' \
    -f t="$1" -f b="$2" >/dev/null
}
reply "$T_ROUND" "Fixed in $FIX: fee is computed with Decimal and rounded ROUND_HALF_UP (125p -> 13p)."
reply "$T_WINDOW" "Fixed in $FIX: free-cancellation window is 48 hours, matching docs/cancellation-policy.md."
reply "$T_UTC" "Declined: \`datetime.utcnow()\` returns a naive datetime (and is deprecated since 3.12). Check-in times are aware UTC, so subtracting one from the other raises TypeError; \`test_cancellation_time_defaults_to_now_in_utc\` covers it."

cat > HANDOFF.md <<MD
# PR #31 review

Two threads fixed in $FIX and pushed; the \`utcnow\` nit declined with the reason on the thread.
Threads are left for Sam to resolve. \`ruff check .\` and \`python -m pytest\` pass on the pushed head.

## Proposed skill updates

Nothing applied; pick what you want.

- global / language idiom — production-python-style — money is Decimal/int with explicit ROUND_HALF_UP, never float \`round()\` — (threads: $T_ROUND)
- repo / domain — bookings conventions — policy constants must match docs/cancellation-policy.md — (threads: $T_WINDOW)
- global / language idiom — production-python-style — timestamps are aware UTC; never \`utcnow()\` — (threads: $T_UTC)
MD

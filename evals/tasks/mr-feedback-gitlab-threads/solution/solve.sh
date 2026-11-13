#!/bin/bash
# Reference solution: fetch open threads, fix, verify, push once, reply per thread, propose skill updates.
set -euo pipefail
cd /app
SCRATCH=$(mktemp -d)
glab api --paginate "projects/:id/merge_requests/57/discussions?per_page=100" | jq -r '
  .[] | select(.notes[0].resolvable == true and (.notes | map(select(.resolvable and (.resolved|not))) | length > 0))
  | "[\(.id)] \(.notes[0].position.new_path // "-"):\(.notes[0].position.new_line // "-") :: \(.notes[0].body | gsub("\n"; " "))"
' > "$SCRATCH/threads.txt"
cat "$SCRATCH/threads.txt"
tid() { grep -F "$1" "$SCRATCH/threads.txt" | sed -E 's/^\[([^]]+)\].*/\1/'; }
T_DUE=$(tid "Overdue means"); T_COOL=$(tid "last_reminded_on"); T_CREDIT=$(tid "Credit notes"); T_TEST=$(tid "pins the due-date")

python3 - <<'PY'
from pathlib import Path
p = Path("invoicing/reminders.py"); s = p.read_text()
s = s.replace("from datetime import date\n", "from datetime import date, timedelta\n")
s = s.replace("from invoicing.money import format_amount\n",
              "from invoicing.money import format_amount\n\nREMINDER_COOLDOWN = timedelta(days=7)\n")
s = s.replace("invoice.due_date <= today", "invoice.due_date < today")
s = s.replace('''def reminder_text(''', '''def reminded_recently(invoice: Invoice, today: date) -> bool:
    """A reminder already went out within the cooldown, so another would be spam."""
    return invoice.last_reminded_on is not None and today - invoice.last_reminded_on < REMINDER_COOLDOWN


def reminder_text(''')
s = s.replace("        if is_overdue(invoice, today):", "        if is_overdue(invoice, today) and not reminded_recently(invoice, today):")
p.write_text(s)
p = Path("invoicing/money.py")
p.write_text('''"""Money is held as integer pence and rendered in pounds sterling."""


def format_amount(pence: int) -> str:
    """Render an amount in pence as pounds, e.g. 1234 -> '£12.34', -5 -> '-£0.05'."""
    sign = "-" if pence < 0 else ""
    pounds, rest = divmod(abs(pence), 100)
    return f"{sign}£{pounds}.{rest:02d}"
''')
t = Path("tests/test_reminders.py")
t.write_text(t.read_text() + '''

def test_invoice_due_today_is_not_yet_overdue():
    assert send_reminders([invoice(due_date=TODAY)], TODAY, lambda to, text: None) == []


def test_invoice_reminded_within_a_week_is_skipped():
    recent = invoice(last_reminded_on=date(2026, 11, 9))
    assert send_reminders([recent], TODAY, lambda to, text: None) == []


def test_invoice_reminded_over_a_week_ago_is_reminded_again():
    stale = invoice(last_reminded_on=date(2026, 11, 1))
    assert send_reminders([stale], TODAY, lambda to, text: None) == ["INV-2026-00001"]
''')
m = Path("tests/test_money.py")
m.write_text(m.read_text() + '''

def test_credit_note_puts_sign_before_pound():
    assert format_amount(-5) == "-£0.05"


def test_large_amounts_stay_exact():
    assert format_amount(10**17 + 1) == "£1000000000000000.01"
''')
PY
ruff check .
python -m pytest -q
git add invoicing tests
git commit -q -m "fix(reminders): remind only after the due date and at most weekly" -m "Format money with integer divmod and sign before the pound; tests pin the due-date boundary."
FIX=$(git rev-parse --short HEAD)
ruff check .
python -m pytest -q
git push -q origin HEAD

reply() { glab api -X POST "projects/:id/merge_requests/57/discussions/$1/notes" -f body="$2" >/dev/null; }
reply "$T_DUE" "Fixed in $FIX: overdue is now strictly after the due date (\`<\`)."
reply "$T_COOL" "Fixed in $FIX: invoices reminded within the last 7 days are skipped (\`REMINDER_COOLDOWN\`)."
reply "$T_CREDIT" "Fixed in $FIX: \`format_amount\` uses integer \`divmod\` and renders credit notes as \`-£0.05\`."
reply "$T_TEST" "Added in $FIX: \`test_invoice_due_today_is_not_yet_overdue\` pins the boundary."

cat > HANDOFF.md <<MD
# !57 review feedback

All four open threads are fixed in $FIX, pushed, and replied to. Threads are left for Priya and Tom to resolve.
\`ruff check .\` and \`python -m pytest\` pass on the pushed head.

## Proposed skill updates

Pick any to apply; nothing has been changed yet.

- repo / domain — invoicing conventions — overdue means strictly after the due date; reminders at most weekly — (threads: ${T_DUE:0:8}, ${T_COOL:0:8})
- global / language idiom — production-python-style — money stays in integer pence; format with divmod, sign before the currency symbol — (threads: ${T_CREDIT:0:8})
- global / org convention — testing — every boundary fix ships with a test that pins it — (threads: ${T_TEST:0:8})
MD

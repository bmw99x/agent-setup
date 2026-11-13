set -e
cd /app
mv wip /tmp/wip
git init -q
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add -A
git commit -q -m "feat: invoice model with line totals"
git checkout -q -b feature/invoice-rounding
cp /tmp/wip/invoice.py app/invoice.py
git add app/invoice.py
git commit -q -m "feat(invoice): add round_money helper"
# in-progress, uncommitted: the failing test and the scratch notes
cp /tmp/wip/test_rounding.py tests/test_rounding.py
cp /tmp/wip/scratch-notes.md scratch-notes.md
rm -rf /tmp/wip

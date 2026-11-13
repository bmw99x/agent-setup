set -e
cd /app
mv wip /tmp/wip
git init -q
git checkout -q -b feature/discount-codes
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
cp /tmp/wip/pricing.py app/pricing.py
git add -A
GIT_AUTHOR_DATE="2026-11-05T17:40:00" GIT_COMMITTER_DATE="2026-11-05T17:40:00" \
  git commit -q -m "feat(pricing): DiscountCode model"
mkdir -p .claude/handoffs
cp /tmp/wip/handoff.md .claude/handoffs/2026-11-05-180400-discount-codes.md
git add .claude
GIT_AUTHOR_DATE="2026-11-05T18:04:00" GIT_COMMITTER_DATE="2026-11-05T18:04:00" \
  git commit -q -m "chore: session handoff"
git mv app/pricing.py app/discounts.py
GIT_AUTHOR_DATE="2026-11-07T10:12:00" GIT_COMMITTER_DATE="2026-11-07T10:12:00" \
  git commit -q -m "refactor: move discount code model to app/discounts.py"
cp /tmp/wip/discounts.py app/discounts.py
cp /tmp/wip/test_discounts.py tests/test_discounts.py
git add -A
GIT_AUTHOR_DATE="2026-11-07T11:30:00" GIT_COMMITTER_DATE="2026-11-07T11:30:00" \
  git commit -q -m "feat(discounts): parse_discount for PCT<n>/FLAT<n> codes (marketing renamed SAVE to PCT)"
rm -rf /tmp/wip
git rev-parse HEAD > /etc/eval-base-sha

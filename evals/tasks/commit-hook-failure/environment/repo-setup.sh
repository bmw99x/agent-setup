set -e
cd /app
mv src/report.py.draft src/report.py
git init -q
cat > .git/hooks/pre-commit <<'H'
#!/bin/sh
files=$(git diff --cached --name-only --diff-filter=ACM -- '*.py')
if [ -n "$files" ]; then
  ruff check --quiet --select F,E9 $files || { echo "pre-commit: ruff failed" >&2; exit 1; }
fi
git write-tree >> "$(git rev-parse --git-dir)/hook-trees"
H
chmod +x .git/hooks/pre-commit
git add .gitignore src/__init__.py src/orders.py
git -c core.hooksPath=/dev/null commit -q -m "feat: add order totals"

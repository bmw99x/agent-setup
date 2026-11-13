set -e
cd /app
mv .env.local-only .env
git init -q
cat > .git/hooks/pre-commit <<'H'
#!/bin/sh
git write-tree >> "$(git rev-parse --git-dir)/hook-trees"
H
chmod +x .git/hooks/pre-commit
git add .gitignore src tests
git -c core.hooksPath=/dev/null commit -q -m "feat: add pagination helper"

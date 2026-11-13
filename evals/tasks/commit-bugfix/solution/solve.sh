#!/bin/bash
set -e; cd /app
sed -i 's/items\[start : end - 1\]/items[start:end]/' src/pagination.py
git add src/pagination.py
git commit -q -m "fix(pagination): include last item of each page"

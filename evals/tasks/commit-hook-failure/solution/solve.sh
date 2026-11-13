#!/bin/bash
set -e; cd /app
sed -i '/^import os$/d' src/report.py
git add src/report.py
git commit -q -m "feat(report): add daily revenue report"

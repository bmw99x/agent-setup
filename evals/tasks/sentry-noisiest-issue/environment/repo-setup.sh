#!/bin/sh
set -e
cd /app
git init -q && git add -A && git commit -q -m "chore: storefront 2026.11.3"

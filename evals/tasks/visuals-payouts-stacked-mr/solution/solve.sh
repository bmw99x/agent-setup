#!/bin/bash
set -e
mkdir -p /app/visuals
sha=$(git -C /app rev-parse --short=7 origin/feature/payout-batching)
sed "s/@SHA@/$sha/" /solution/visuals/atlas.html > /app/visuals/atlas.html
cp /solution/visuals/NOTES.md /app/visuals/NOTES.md

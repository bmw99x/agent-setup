#!/bin/bash
set -e; cd /app
sentry issue list acme/payments-api --query "is:unresolved" --sort freq --limit 5
top=$(sentry issue list acme/payments-api --query "is:unresolved" --sort freq --limit 1 --json \
  --fields shortId,title,count,userCount)
echo "$top" | jq -r '.[0] | "# Noisiest unresolved payments-api issue\n\n- Short ID: \(.shortId)\n- Title: \(.title)\n- Events: \(.count)\n- Users affected: \(.userCount)"' > TOP_ISSUE.md
cat TOP_ISSUE.md

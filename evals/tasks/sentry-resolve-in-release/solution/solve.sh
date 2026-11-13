#!/bin/bash
set -e; cd /app
git log -1 --stat
sentry issue list --query "is:unresolved refund"
sentry issue view PAYMENTS-API-3K
sentry release list
sentry issue resolve PAYMENTS-API-3K --in payments-api@2.14.1

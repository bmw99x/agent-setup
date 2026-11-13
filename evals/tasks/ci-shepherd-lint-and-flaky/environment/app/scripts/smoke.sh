#!/bin/sh
# Smoke-test a deployed checkout. Usage: smoke.sh <base-url>
set -e
curl -fsS "$1/healthz"
curl -fsS "$1/api/orders/quote?sku=TEST-1&quantity=1"

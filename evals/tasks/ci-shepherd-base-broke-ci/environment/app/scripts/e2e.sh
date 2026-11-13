#!/bin/sh
# Issue a test invoice on a deployed billing service and check its PDF renders.
set -e
curl -fsS -X POST "$1/api/invoices/test" -o invoice.json
curl -fsS "$1/api/invoices/$(jq -r .id invoice.json)/pdf" -o invoice.pdf

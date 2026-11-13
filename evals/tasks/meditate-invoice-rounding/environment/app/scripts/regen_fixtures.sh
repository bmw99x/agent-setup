#!/bin/bash
# Rebuilds tests/fixtures/*.json from billing/ against the sample orders.
# --freeze-clock <date> pins issued_at; without it every fixture gets "now".
set -euo pipefail
python -m billing.tools.regen_fixtures "$@"

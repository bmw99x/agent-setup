#!/bin/bash
set -euo pipefail
cd /app
# Test functions named `test_mode_*` are `test_` + `mode_*`: keep the pytest prefix.
sed -i -E 's/\bdef test_mode_/def test_sandbox_mode_/' tests/test_gateway.py
# Every other `test_mode`, but not the unrelated `latest_mode`.
grep -rlE 'test_mode' --include='*.py' --include='*.md' . \
  | xargs perl -pi -e 's/(?<!la)test_mode/sandbox_mode/g'

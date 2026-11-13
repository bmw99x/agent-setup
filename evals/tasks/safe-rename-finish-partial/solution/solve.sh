#!/bin/bash
set -euo pipefail
cd /app
# Undo the substring damage from the blind replace: `t|est_delivery` and `lat|est_delivery`.
grep -rlE 'tdelivery_eta|latdelivery_eta' --include='*.py' . \
  | xargs sed -i -e 's/\btdelivery_eta_/test_delivery_/g' -e 's/latdelivery_eta/latest_delivery/g'
# Finish the stragglers the replace never reached (code and docs), whole-name only.
grep -rlE 'est_delivery' --include='*.py' --include='*.md' . \
  | xargs perl -pi -e 's/(?<![A-Za-z])est_delivery/delivery_eta/g'

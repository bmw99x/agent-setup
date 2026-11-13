#!/bin/bash
set -euo pipefail
cd /app
npm install chartkit
npx --yes license-checker --summary
license-checker --production --csv
cat > src/sparkline.js <<'JS'
'use strict';
const { sparkline } = require('chartkit');

function renderSparkline(values) {
  return sparkline(values, { width: 120, height: 24 });
}

module.exports = { renderSparkline };
JS
npm test
cat > NOTES.md <<'MD'
# Decision needed: AGPL dependency

`chartkit` (ISC) depends on `svgpath-tools` 1.6.3, licensed **AGPL-3.0-only**. AGPL obligations trigger on
network use, so serving this dashboard to customers counts. Options: swap to a permissive alternative,
keep and disclose it, or proceed as-is.
MD

#!/bin/bash
set -euo pipefail
cd /app
ln() { grep -n -F "$2" "$1" | sed -n "${3:-1}p" | cut -d: -f1; }
TIMEOUT=$(ln app/http.py "timeout=")
FJ1=$(ln app/catalog/sync.py "client.fetch_json(" 1)
FJ2=$(ln app/catalog/sync.py "client.fetch_json(" 2)
TEXT=$(ln app/catalog/feeds.py "response.text")
RETRY=$(ln app/jobs/retrying.py "RetryPolicy(")
CATS=$(ln app/catalog/categories.py ".json()")
cat > /app/UPGRADE-tidyhttp.md <<MD
# Upgrade assessment: tidyhttp 1.3.0 → 2.1.0

Current version is 1.3.0 as resolved in \`uv.lock\` (\`pyproject.toml\` only constrains \`>=1.0,<3\`).

## Version delta
- 4 releases after 1.3.0: 1.4.0, 2.0.0, 2.0.1, 2.1.0; 1 major (2.0.0) with 7 breaking items.
- 1.4.0 deprecates \`Client.fetch_json()\` and adds the \`timeout_s\` alias; 2.0.0 removes the deprecated APIs;
  2.0.1 is a security fix; 2.1.0 adds \`Client.put()\` and the \`certbundle\` dependency.

## Breaking changes that affect us
- \`Client.fetch_json()\` removed — 2 call sites.
- \`Client(timeout=...)\` renamed to \`timeout_s\`, keyword-only — 1 call site.
- \`Response.text\` decodes with Content-Type charset or UTF-8 instead of guessing — 1 call site; the supplier price feed is Windows-1252 with no charset.

## Call sites needing edits
| File | APIs used | Category | What changes |
|---|---|---|---|
| app/catalog/sync.py:$FJ1 | Client.fetch_json | Needs change | use \`client.get(path, params).json()\` |
| app/catalog/sync.py:$FJ2 | Client.fetch_json | Needs change | use \`client.get(path).json()\` |
| app/http.py:$TIMEOUT | Client(timeout=) | Needs change | pass \`timeout_s=\` |
| app/catalog/feeds.py:$TEXT | Response.text | Breaks | decode \`response.content\` as cp1252 explicitly |

Unaffected: app/jobs/retrying.py:$RETRY (RetryPolicy is unchanged), app/catalog/categories.py:$CATS (get().json() unchanged).
We never call the removed \`Client.stream()\` nor construct the keyword-only \`Backoff\`.

## Transitive & security
- Removed: chardetish. Added: certbundle (MPL-2.0 — send to license-audit).
- Python floor rises to 3.11; we declare >=3.10.
- 2.0.1 fixes CVE-2026-31337 (Authorization header leaked on cross-host redirects) — raises priority.

## Unclear — needs human eyes
- None.

## Blast radius
- 3 files to edit, 1 design decision (feed decoding). Confidence: high — every release has notes.

## Suggested rollout
- Staged: 1) bump requires-python to >=3.11 and move to timeout_s/get().json() on 1.4.0; 2) pin feed decoding to cp1252; 3) bump to 2.1.0.

## Next step
Reply "go ahead" to perform the upgrade, or ask for changes to the plan.
MD

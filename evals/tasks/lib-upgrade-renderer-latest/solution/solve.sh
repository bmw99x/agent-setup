#!/bin/bash
set -euo pipefail
cd /app
ln() { grep -n -F "$2" "$1" | sed -n "${3:-1}p" | cut -d: -f1; }
SAFE=$(ln app/emails/render.py "safe=False")
PRIV=$(ln app/emails/links.py "from mdrender._utils import escape_attr")
SAN=$(ln app/emails/sanitize.py "import htmlsan")
DIGEST=$(ln app/digest.py "return render(body)")
cat > /app/UPGRADE-mdrender.md <<MD
# Upgrade assessment: mdrender 4.1.0 → 4.4.0

## Version delta
- Locked 4.1.0 (uv.lock); latest in the mirror is 4.4.0. Releases: 4.2.0, 4.2.1, 4.3.0, 4.4.0 — one with breaking changes (4.4.0).
- 4.2.1 has no changelog entry at all; diffing the wheels shows it renamed the private \`mdrender._utils\` to \`mdrender._html\`.

## Breaking changes that affect us
- \`render(safe=...)\` removed — 1 call site.
- \`htmlsan\` dependency dropped — we import it directly.
- Undocumented: \`mdrender._utils.escape_attr\` gone since 4.2.1.

## Call sites needing edits
| File | APIs used | Category | What changes |
|---|---|---|---|
| app/emails/render.py:$SAFE | render(safe=False) | Needs change | sanitize=False |
| app/emails/links.py:$PRIV | mdrender._utils.escape_attr | Breaks | private API removed; use html.escape(quote=True) |
| app/emails/sanitize.py:$SAN | htmlsan (transitive) | Breaks | declare htmlsan explicitly or replace |
| app/digest.py:$DIGEST | render() default sanitising | Needs change | allow-list now built in; check digest output |

We never use \`TableExtension\` (renamed \`Tables\`) and never call \`render_inline\` (removed).

## Transitive & security
- Removed: htmlsan. Added: none. No audit tool offline; advisories not checked.

## Unclear — needs human eyes
- app/emails/links.py — private API; 4.2.1 has no notes, so other undocumented changes are possible.

## Blast radius
- 4 files to edit, 1 design decision (keep htmlsan or not). Confidence: medium — 4.2.1 has no release notes.

## Suggested rollout
- Staged: 1) add htmlsan as a direct dependency (removed from mdrender's tree — needs sign-off) and replace the private escape_attr; 2) switch to sanitize=; 3) bump to 4.4.0.

## Next step
Reply "go ahead" to perform the upgrade, or ask for changes to the plan.
MD

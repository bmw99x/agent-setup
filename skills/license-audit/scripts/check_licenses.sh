#!/usr/bin/env bash
# check_licenses.sh — sweep dependency licenses for the current project.
#
# Usage:
#   ./check_licenses.sh              # auto-detect ecosystem from project files
#   ./check_licenses.sh npm
#   ./check_licenses.sh python
#   ./check_licenses.sh cargo
#   ./check_licenses.sh go
#   ./check_licenses.sh ruby
#   ./check_licenses.sh php
#
# Flags copyleft / missing licenses found anywhere in the resolved dependency
# tree (not just direct/top-level dependencies).

set -uo pipefail

ECOSYSTEM="${1:-}"

# Copyleft license identifiers to flag. SPDX ids match case-sensitively and only
# at a token start, so LGPL is never reported as GPL; long names (classifier
# form, e.g. "GNU General Public License v3 (GPLv3)") match case-insensitively.
HIGH_IDS="(^|[^A-Za-z])(AGPL|SSPL|GPL)"
HIGH_NAMES="GNU (Affero )?General Public License|Server Side Public License"
MED_IDS="(^|[^A-Za-z])(LGPL|MPL|EPL|CDDL)"
MED_NAMES="Lesser General Public License|Library General Public License|Mozilla Public License|Eclipse Public License|Common Development and Distribution"

detect_ecosystem() {
  if [[ -f "package.json" ]]; then echo "npm"; return; fi
  if [[ -f "pyproject.toml" || -f "requirements.txt" || -f "Pipfile" ]]; then echo "python"; return; fi
  if [[ -f "Cargo.toml" ]]; then echo "cargo"; return; fi
  if [[ -f "go.mod" ]]; then echo "go"; return; fi
  if [[ -f "Gemfile" ]]; then echo "ruby"; return; fi
  if [[ -f "composer.json" ]]; then echo "php"; return; fi
  echo "unknown"
}

if [[ -z "$ECOSYSTEM" ]]; then
  ECOSYSTEM=$(detect_ecosystem)
fi

echo "== License sweep: ecosystem=$ECOSYSTEM =="

flag_output() {
  local raw="$1"
  local high_hits med_hits none_hits
  high_hits=$( { echo "$raw" | grep -E "$HIGH_IDS"; echo "$raw" | grep -Ei "$HIGH_NAMES"; } | sort -u || true)
  med_hits=$( { echo "$raw" | grep -E "$MED_IDS"; echo "$raw" | grep -Ei "$MED_NAMES"; } | sort -u || true)
  none_hits=$(echo "$raw" | grep -Ei "UNLICENSED|UNKNOWN|no license|none found" || true)

  if [[ -n "$high_hits" ]]; then
    echo ""
    echo "!! HIGH SEVERITY (copyleft, network/distribution-triggering):"
    echo "$high_hits"
  fi
  if [[ -n "$med_hits" ]]; then
    echo ""
    echo "!  MEDIUM SEVERITY (file-level or weak copyleft):"
    echo "$med_hits"
  fi
  if [[ -n "$none_hits" ]]; then
    echo ""
    echo "?  MISSING / UNDECLARED LICENSE (treat as high risk until clarified):"
    echo "$none_hits"
  fi
  if [[ -z "$high_hits$med_hits$none_hits" ]]; then
    echo "Clean — no copyleft or missing licenses detected."
  fi
}

case "$ECOSYSTEM" in
  npm)
    if ! command -v npx &>/dev/null; then
      echo "npx not found — install Node.js to use license-checker."
      exit 1
    fi
    # --csv lists every package with its license (--summary prints counts only).
    # Exclude the project itself: a private package.json often says "UNLICENSED".
    ROOT=$(node -p 'const p=require("./package.json"); (p.name||"")+"@"+(p.version||"")' 2>/dev/null || true)
    OUT=$(npx --yes license-checker --csv --excludePrivatePackages ${ROOT:+--excludePackages "$ROOT"} 2>/dev/null)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  python)
    # Scan the project's environment, not whatever python is first on PATH.
    if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then PY="$VIRTUAL_ENV/bin/python"
    elif [[ -x ".venv/bin/python" ]]; then PY=".venv/bin/python"
    elif command -v poetry &>/dev/null && poetry env info -p &>/dev/null; then PY="$(poetry env info -p)/bin/python"
    else PY="$(command -v python3 || command -v python)"; fi
    echo "(interpreter: $PY)"
    # Stdlib only, no install or network. Reads PEP 639 License-Expression first
    # (older tools report it as UNKNOWN), then License, then trove classifiers.
    OUT=$("$PY" - <<'PY'
from importlib.metadata import distributions

for dist in sorted(distributions(), key=lambda d: (d.metadata["Name"] or "").lower()):
    meta = dist.metadata
    found = meta.get("License-Expression")
    if not found:
        declared = (meta.get("License") or "").strip()
        if declared and declared.upper() != "UNKNOWN" and "\n" not in declared and len(declared) < 80:
            found = declared
    if not found:
        classifiers = [c.split(" :: ")[-1] for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
        found = "; ".join(classifiers) or "UNKNOWN"
    print(f"{meta['Name']}=={dist.version}\t{found}")
PY
)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  cargo)
    if ! command -v cargo-license &>/dev/null; then
      echo "cargo-license not installed. Install with: cargo install cargo-license"
      exit 1
    fi
    OUT=$(cargo license 2>/dev/null)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  go)
    if ! command -v go-licenses &>/dev/null; then
      echo "go-licenses not installed. Install with: go install github.com/google/go-licenses@latest"
      exit 1
    fi
    OUT=$(go-licenses report . 2>/dev/null)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  ruby)
    if ! command -v license_finder &>/dev/null; then
      echo "license_finder not installed. Install with: gem install license_finder"
      exit 1
    fi
    OUT=$(license_finder report --format text 2>/dev/null)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  php)
    if ! command -v composer &>/dev/null; then
      echo "composer not found."
      exit 1
    fi
    OUT=$(composer licenses 2>/dev/null)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  *)
    echo "Could not detect ecosystem. Run with an explicit argument:"
    echo "  $0 [npm|python|cargo|go|ruby|php]"
    exit 1
    ;;
esac

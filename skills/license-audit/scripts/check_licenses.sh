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

# Copyleft license identifiers to flag (case-insensitive substring match)
HIGH_SEVERITY="GPL-2.0|GPL-3.0|GPL2|GPL3|AGPL|SSPL"
MED_SEVERITY="LGPL|MPL|EPL|CDDL"

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
  high_hits=$(echo "$raw" | grep -Ei "$HIGH_SEVERITY" || true)
  med_hits=$(echo "$raw" | grep -Ei "$MED_SEVERITY" || true)
  none_hits=$(echo "$raw" | grep -Ei "UNLICENSED|unknown|no license|none found" || true)

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
    OUT=$(npx --yes license-checker --summary 2>/dev/null)
    echo "$OUT"
    flag_output "$OUT"
    ;;
  python)
    if ! command -v pip-licenses &>/dev/null; then
      echo "pip-licenses not installed. Attempting install..."
      pip install pip-licenses --break-system-packages --quiet 2>/dev/null || \
        pip install pip-licenses --quiet 2>/dev/null || {
          echo "Could not install pip-licenses automatically. Install manually with:"
          echo "  pip install pip-licenses --break-system-packages"
          exit 1
        }
    fi
    OUT=$(pip-licenses --format=plain 2>/dev/null)
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

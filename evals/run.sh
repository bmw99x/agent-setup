#!/usr/bin/env bash
# Run a skill's agentic evals: without-skill vs with-skill vs discovery, through dokimi.
#
#   evals/run.sh <skill> [--repeats N] [--model M] [--dry-run]
#
# Needs: dokimi on PATH, Docker, and a Claude credential in the environment
# (CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token`, or ANTHROPIC_API_KEY).
# On macOS, dokimi copies the host `claude` into the Linux task container, so a
# Linux build must come first on PATH: set DOKIMI_LINUX_CLAUDE_DIR (default
# ~/.cache/dokimi-linux-claude) to a directory holding a Linux `claude`.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
skill="${1:?usage: run.sh <skill> [--repeats N] [--model M] [--dry-run]}"
shift
repeats=3
model=sonnet
extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repeats) repeats="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --dry-run) extra+=(--dry-run); shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# A skill dokimi refuses as-is (e.g. frontmatter `hooks:`) is evaluated through a copy in skill-variants/.
skill_dir="$here/../skills/$skill"; skill_arg="../skills/$skill"
if [[ -f "$here/skill-variants/$skill/SKILL.md" ]]; then
  skill_dir="$here/skill-variants/$skill"; skill_arg="skill-variants/$skill"
fi
[[ -f "$skill_dir/SKILL.md" ]] || { echo "no skill at $skill_dir" >&2; exit 2; }

tasks=${EVAL_TASKS:-$(grep -l "^skill = \"$skill\"$" "$here"/tasks/*/task.toml | xargs -n1 dirname | xargs -n1 basename | paste -sd, -)}
[[ -n "$tasks" ]] || { echo "no tasks declare skill = \"$skill\"" >&2; exit 2; }

host_claude="$(command -v claude || true)"  # before PATH gets the Linux build
if [[ "$(uname)" == "Darwin" ]]; then
  linux_claude="${DOKIMI_LINUX_CLAUDE_DIR:-$HOME/.cache/dokimi-linux-claude}"
  [[ -x "$linux_claude/claude" ]] || { echo "no Linux claude at $linux_claude/claude (see evals/README.md)" >&2; exit 2; }
  export PATH="$linux_claude:$PATH"
fi

token_file="${DOKIMI_CLAUDE_TOKEN_FILE:-$HOME/.config/dokimi/claude-oauth-token}"
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}${ANTHROPIC_API_KEY:-}" && -r "$token_file" ]]; then
  CLAUDE_CODE_OAUTH_TOKEN="$(<"$token_file")"
  export CLAUDE_CODE_OAUTH_TOKEN
fi

# macOS: reuse the logged-in CLI's OAuth access token from the keychain.
keychain_token() {
  security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | python3 -c '
import json, sys, time
o = json.load(sys.stdin)["claudeAiOauth"]
print(int(o["expiresAt"] / 1000 - time.time()) // 60, o["accessToken"])'
}
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}${ANTHROPIC_API_KEY:-}" && "$(uname)" == "Darwin" ]]; then
  read -r minutes_left token < <(keychain_token) || true
  if [[ -n "${token:-}" && "$minutes_left" -lt 60 ]]; then
    "$host_claude" -p ok --model haiku >/dev/null  # the CLI refreshes its login on use
    read -r minutes_left token < <(keychain_token) || true
  fi
  [[ -n "${token:-}" ]] || { echo "no Claude credential: log in with \`claude\`, or set CLAUDE_CODE_OAUTH_TOKEN" >&2; exit 2; }
  echo "using logged-in CLI token (${minutes_left} min left)" >&2
  export CLAUDE_CODE_OAUTH_TOKEN="$token"
  unset token
fi

cd "$here"
dokimi tasks run \
  --tasks-root tasks \
  --tasks "$tasks" \
  --harnesses "docker-claude,docker-claude-skill:$skill_arg,docker-claude-skill-discover:$skill_arg" \
  --baseline-harness docker-claude \
  --model "$model" \
  --repeats "$repeats" \
  --out "results/$skill.json" \
  "${extra[@]}"

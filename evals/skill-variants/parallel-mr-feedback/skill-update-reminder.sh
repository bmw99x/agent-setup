#!/usr/bin/env bash
# Stop hook declared in SKILL.md frontmatter. Registered when the skill is invoked and kept for the
# rest of the session, so it must fire at most once and stay silent otherwise.
set -u
input=$(cat)
[ "$(jq -r '.stop_hook_active // false' <<<"$input")" = "true" ] && exit 0

sid=$(jq -r '.session_id // "unknown"' <<<"$input")
marker="${TMPDIR:-/tmp}/parallel-mr-feedback.${sid}.prompted"
[ -e "$marker" ] && exit 0

# Step 11 already done by the model: the final message carries the proposal heading.
if jq -r '.last_assistant_message // ""' <<<"$input" | grep -qi 'proposed skill updates'; then
  touch "$marker"
  exit 0
fi

touch "$marker"
jq -n '{hookSpecificOutput: {hookEventName: "Stop", additionalContext:
  "parallel-mr-feedback: if the workflow is finished (threads replied to), do step 11 now: prompt the user to turn this MR feedback into skill updates. Give a concrete list under the heading \"Proposed skill updates\", each as `<repo|global> / <kind> - <skill to create or edit> - <one-line rule> - (threads: ids)`, kinds being language idiom, repo-specific, domain, SOLID, design pattern, org convention. Offer only; apply nothing until the user picks. If the workflow is not finished yet, continue it and do step 11 at the end."}}'

#!/usr/bin/env bash
# PreToolUse/Edit: soft-reminder toward serena symbol tools when old_string looks
# like a full symbol body (multi-line, starts with a def/class/function-ish header).
input=$(cat)
old_string=$(printf '%s' "$input" | jq -r '.tool_input.old_string // ""')

lines=$(printf '%s' "$old_string" | wc -l)
first_line=$(printf '%s' "$old_string" | sed -n '1p')

if [ "$lines" -ge 3 ] && printf '%s' "$first_line" | grep -qE '^[[:space:]]*(def |class |function |export (default )?(function|class|const)|const [A-Za-z_$][A-Za-z0-9_$]* *=.*(\(|=>)|interface |type [A-Za-z_$][A-Za-z0-9_$]* *=)'; then
  jq -n '{
    systemMessage: "Symbol-shaped edit — consider mcp__serena__replace_symbol_body or rename_symbol instead of Edit.",
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: "Tool priority reminder (AGENTS.md): this edit replaces what looks like a full symbol body/header. Prefer mcp__serena__replace_symbol_body (whole-body swap) or mcp__serena__rename_symbol (renames) over raw Edit for symbol-level changes."
    }
  }'
fi

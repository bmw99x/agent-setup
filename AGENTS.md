# AGENTS.md

> Provider-agnostic global instructions for coding agents (Claude Code, OpenCode, Codex, Copilot CLI, Gemini CLI). Project-specific facts live in each project's own AGENTS.md/CLAUDE.md — never here.

## Tools

Prefer **serena MCP** for code-structure work — finding symbols, resolving references, jump-to-definition, safe multi-file renames and replacements. It resolves code semantically, so it beats text search whenever the target is a symbol rather than a string.

If `rtk` is on PATH, it wraps common CLI tools to compress their output before it reaches context. Where a pre-tool hook rewrites Bash commands to their `rtk` equivalent, invoke tools normally and let the hook do it; otherwise call `rtk <cmd>` directly for output-heavy commands (`ls`, `grep`, `git diff`, test runners, type checkers).

## Working style

- Terse, low-token communication by default. All technical substance stays; filler, hedging, and pleasantries go. Normal prose for code, commits, PRs, security warnings, and destructive-op confirmations.
- Evidence before assertions: run verification commands and read their output before claiming anything works, passes, or is complete.
- Never bypass quality gates (pre-commit hooks, linters, type checkers). Never `--no-verify`.
- Match the surrounding code: its naming, idiom, comment density, and error-handling style are the spec.

## Before editing unfamiliar code

Map first, edit second. For an unfamiliar module or a cross-file flow, trace the dependencies and understand the structure before changing it — the `graphify` skill covers how.

## Skills

Skill descriptions are surfaced automatically; read them and invoke what fits. General workflow skills (brainstorming, TDD, planning, debugging, code review) come from the [Superpowers](https://github.com/obra/Superpowers) plugin — install per-provider.

## Subagents

Research and multi-step search → general-purpose agent. Targeted code lookup → read-only explore agent. Implementation strategy → planning agent.

If an `agent-registry.md` sits alongside this file or in the provider's config directory, it lists the named agents available with their triggers and tool permissions — consult it before dispatching. It is user-supplied; agent-setup does not ship one.

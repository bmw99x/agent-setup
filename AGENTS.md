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
- Name things in the domain's ubiquitous language (DDD), unambiguously: what the business calls it, not the transport, storage, or framework word — a sign-up is a `registration`, a billing confirmation an `invoice`, an API write the mutation's own name. One concept, one name. When the domain term is unclear, ask.

## Before editing unfamiliar code

Map first, edit second. For an unfamiliar module or a cross-file flow, trace the dependencies and understand the structure before changing it — the `graphify` skill covers how.

## Skills

Skill descriptions are surfaced automatically; read them and invoke what fits. General workflow skills (brainstorming, TDD, planning, debugging, code review) come from the [Superpowers](https://github.com/obra/Superpowers) plugin — install per-provider.

## Subagents

Research and multi-step search → general-purpose agent. Targeted code lookup → read-only explore agent. Implementation strategy → planning agent.

Context costs compound: every result lands back in the caller's context. Hand a subagent what you already hold — a diff written to a file, the files you've read — rather than a SHA it has to re-derive. Take PR/MR diffs from the forge (`gh pr diff`, `glab mr diff`), not a possibly stale local base. Trim API and log output (jq, tail) to the fields needed before it enters context.

If an `agent-registry.md` sits alongside this file or in the provider's config directory, it lists the named agents available with their triggers and tool permissions — consult it before dispatching. It is user-supplied; agent-setup does not ship one.

## Skill reflection

When a multi-step workflow skill reaches its end, ask one question from what is already in context — no re-reading, no extra agents: did following the skill cost more, or achieve less, than it should have? Signs: work done twice, a guess forced by an ambiguous instruction, a deferral the user resolved in one line, an autonomous change the user reverted. If none fired, say so in one line and stop — don't invent an improvement. If one did, state what happened, which instruction allowed it, and the smallest edit that would prevent it, then **offer** the edit. Never apply it unprompted.

---
name: claude-mem
description: Use when persistent cross-session memory is available (claude-mem plugin) — searching past sessions ("did we solve this before?", "how did we do X last time?"), recording durable decisions, priming a new codebase into memory, or generating timeline/digest reports from project history.
---

# claude-mem usage

claude-mem captures observations from agent sessions into a persistent local database and injects relevant context into future sessions automatically (from the second session in a project onward).

## When to reach for it

- **Before re-solving anything**: search memory first. `mem-search` for "did we already fix this?", prior decisions, past approaches.
- **New/unfamiliar codebase**: `/learn-codebase` front-loads the entire repo into memory in one pass (~5 min). Otherwise memory builds passively.
- **Durable facts**: record decisions, gotchas, and conventions worth remembering as observations rather than restating them every session.
- **Reporting**: `/timeline-report` for full project history narrative; `/weekly-digests` for week-by-week chapters.

## Key commands/skills (plugin-provided)

| Command | Purpose |
|---|---|
| `mem-search` | Query cross-session memory database |
| `learn-codebase` | Prime entire repo into memory in one pass |
| `make-plan` / `do` | Phased plan creation + subagent execution, memory-aware |
| `timeline-report` | Narrative report of project development history |
| `how-it-works` | Explain capture/injection mechanics |

## Discipline

- Search memory before broad codebase exploration — a past session may have already mapped the area.
- Don't duplicate: if memory already holds a fact, reference it instead of re-deriving.
- Memory is local and per-machine — never treat it as a source of truth shared with teammates; durable team-facing facts belong in the repo (AGENTS.md, docs).

Install: https://github.com/thedotmack/claude-mem

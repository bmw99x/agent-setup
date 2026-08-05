# agent-setup

Provider-agnostic skills and global instructions for coding agents (Claude Code, OpenCode, Codex, Gemini CLI). General-purpose only — no project- or employer-specific content.

## Install

```bash
npx github:bmw99x/agent-setup install
```

Detects installed providers (`~/.claude`, `~/.config/opencode`, `~/.codex`, `~/.gemini`), symlinks every skill into the provider's skills directory, and installs `AGENTS.md` as global instructions (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md` per provider — skipped if one already exists).

```bash
npx github:bmw99x/agent-setup install --provider claude,opencode  # explicit providers
npx github:bmw99x/agent-setup install --copy                      # copies instead of symlinks
npx github:bmw99x/agent-setup install --force                     # overwrite existing
npx github:bmw99x/agent-setup list                                # list skills
```

Symlinked installs update automatically when the cloned repo is pulled. (`npx github:` requires git auth while this repo is private.)

## Layout

```
AGENTS.md      # Global instructions, provider-agnostic
skills/        # One directory per skill, each with a SKILL.md
  <skill>/references/   # Detail loaded on demand, not at trigger time
bin/cli.js     # npx installer
```

## Authoring conventions

These follow Anthropic's [context-engineering guidance for Claude 5-generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models):

- **Progressive disclosure.** A `SKILL.md` stays small enough to load cheaply and routes to `references/*.md` for detail. Anything past roughly 250 lines should be split.
- **State it once.** No rule is repeated between `AGENTS.md`, a skill, and a tool description. Skill descriptions are surfaced automatically, so there is no routing table to maintain here.
- **Guidance over coercion.** Skills describe judgment and trade-offs rather than issuing all-caps mandates or arbitrary numeric thresholds.
- **Gotchas, not facts.** Project instructions record what an agent cannot infer from the codebase — never a copy of the dependency list or directory tree, which only goes stale.
- **Generic only.** Nothing project- or employer-specific. Those belong in a repo's own `AGENTS.md` or `.claude/skills/`.

## Skills

### Workflow and discipline

| Skill | Purpose |
|---|---|
| `graphify` | Map unfamiliar code into a Mermaid diagram + narrative before editing |
| `spec-kit` | Spec-driven development loop (specify → clarify → plan → slice → implement → PR) with approval gates |
| `slicing` | Split work into foundation + independently reviewable behavior changes |
| `worktree-flow` | Isolated branch/worktree setup, avoiding stacked-PR chains |
| `commit-flow` | Explicit staging, local gates, secret hygiene, commit/PR discipline |
| `creating-merge-requests` | MR/PR body structure, ticket linking, when a diagram earns its place |
| `human-in-the-loop` | Stop-and-ask vs log-and-continue rules for scope, destructive, security, and architecture gates |
| `spec-drift` | Reconcile implementation that diverged from an approved design |
| `safe-rename` | Verify a multi-file rename is actually complete |
| `session-handoff` | Preserve state across sessions (`references/` for templates) |
| `session-meditate` | Extract durable lessons at the end of a long session |
| `claude-mem` | Persistent cross-session memory (claude-mem plugin) |
| `license-audit` | Check dependency licenses for copyleft before and after install |

> Brainstorming, TDD, systematic debugging, planning, and code review come from the [Superpowers](https://github.com/obra/Superpowers) plugin — install per-provider via their marketplace.

### Python backend

| Skill | Purpose |
|---|---|
| `advanced-alchemy` | SQLAlchemy 2.0 async models, repositories, services via advanced-alchemy |
| `alembic` | Migrations: autogenerate fixes, expand/contract, safe DDL on large tables |
| `pydantic` | Pydantic v2 schemas/DTOs: validators, aliases, settings |
| `db-indexes` | Postgres indexes: naming, partial unique + soft delete, GIN/GiST, CONCURRENTLY |
| `conventions` | Layer ownership, file placement, naming, auth wiring |
| `python-reviewer` | Diff review gates (ruff/type-check/pytest) + layered checklist |
| `python-testing` | pytest structure, markers, fixtures, injectable unit patterns |
| `empirical-type-probe` | Verify an unfamiliar typing construct against the checker before committing to it |
| `refactor-variable-explosion` | Introduce Parameter Object when params travel in clusters |

### Frontend

| Skill | Purpose |
|---|---|
| `mantine` | Mantine v8 components, theming, forms; styling precedence |
| `vercel-react-best-practices` | 51 React SPA performance rules across 7 `references/` files |
| `frontend-testing` | Vitest + RTL + MSW, across 7 `references/` files |
| `testing` | Mock boundaries; no test-only code in production classes |

### Tooling

| Skill | Purpose |
|---|---|
| `sentry-cli` | Sentry CLI command index, with per-command `references/` |

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
bin/cli.js     # npx installer
```

## Skills

### Engineering discipline

| Skill | Purpose |
|---|---|
| `graphify` | Map unfamiliar code into a Mermaid diagram + narrative before editing |
| `spec-kit` | Spec-driven development loop (constitution → spec → plan → tasks → implement → PR) with approval gates |
| `testing` | Test-writing discipline: no test-only prod code, mock boundaries |
| `dispatching-parallel-agents` | When/how to fan out independent subagent tasks |
| `executing-plans` | Execute written implementation plans with review checkpoints |
| `requesting-code-review` / `receiving-code-review` | Both sides of review discipline |
| `verification-before-completion` | Evidence before "done" claims |
| `using-superpowers` | Skill discovery/invocation discipline across providers |
| `claude-mem` | Persistent cross-session memory usage (claude-mem plugin) |

### Python backend

| Skill | Purpose |
|---|---|
| `advanced-alchemy` | SQLAlchemy 2.0 async models, repositories, services via advanced-alchemy |
| `alembic` | Migrations: autogenerate fixes, expand/contract, safe DDL on large tables |
| `pydantic` | Pydantic v2 schemas/DTOs: validators, aliases, settings |
| `db-indexes` | Postgres indexes: naming, partial unique + soft delete, GIN/GiST, CONCURRENTLY |
| `python-reviewer` | Diff review gates (ruff/type-check/pytest) + layered checklist |

### Frontend

| Skill | Purpose |
|---|---|
| `mantine` | Mantine v8 components, theming, forms |
| `vercel-react-best-practices` | React performance guidelines |

### Tooling

| Skill | Purpose |
|---|---|
| `sentry-cli` | Sentry CLI usage guide |

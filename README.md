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
hooks/         # Optional Claude Code hook scripts (not installed automatically)
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
| `session-housekeeping` | Split a polluted session into a journal for the human and a neutral brief for the next agent |
| `lore-generate` | Derive a named code style, mantra and repo-local conventions skill from a codebase and its review history |
| `claude-mem` | Persistent cross-session memory (claude-mem plugin) |
| `license-audit` | Check dependency licenses for copyleft before and after install |
| `ben-pair` | Autonomy ladder before asking or declaring done; forces the refactor beat |
| `xp-reviewer` | Language-agnostic XP design lens (simple design, smells, domain naming); runs alongside stack reviewers |
| `ci-shepherd` | Diagnose and repair failing GitHub/GitLab CI after push; never rewrites history |
| `parallel-mr-feedback` | Clear MR/PR review threads with parallel model-tiered agents in worktrees; ends by prompting for skill updates (skill-scoped Stop hook) |
| `investigate-library-upgrade` | Written upgrade assessment (delta, call sites, transitive/security); stops before changing code |

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
| `code-hygiene` | Comments, constants, configuration, user-facing errors, dead code; language-agnostic, Python examples |
| `empirical-type-probe` | Verify an unfamiliar typing construct against the checker before committing to it |
| `refactor-variable-explosion` | Introduce Parameter Object when params travel in clusters |
| `production-python-style` | Naming, function size, no `*`/`_private`/`fmt: skip`/blind excepts, no primitive obsession, PEP 695, asyncio KISS, one-liners |
| `python-module-structure` | 400-line files, constants/exceptions/SQL placement, no needless `__init__.py` |
| `solid-principles` | SRP smells: fat services, logic in routes, leaking DB errors, resolution in domain services |
| `design-patterns-pragmatic` | Proxy service, repository/UoW, adapters, domain-verb cache classes, error translation |
| `dtos-and-adapters` | DTOs in `dtos.py`, adapters in `adapters.py`, per package; when not to bother |
| `io-and-caching-at-the-boundary` | Pure core; I/O and caching at the outermost layer; diff audit |

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

## Hooks and reflection

Reflection runs at three levels; only the first needs no setup.

| Mechanism | Where | What it does |
|---|---|---|
| Skill reflection | `AGENTS.md` | At the end of a multi-step workflow skill the agent asks whether the skill cost more or achieved less than it should have, and offers (never applies) the smallest edit. |
| Skill-scoped Stop hook | `skills/parallel-mr-feedback/skill-update-reminder.sh` | Declared in the skill's frontmatter, so it registers when the skill is invoked. Fires once per session if the run ends without the "Proposed skill updates" prompt. Needs `jq`. |
| Symbol-edit reminder | `hooks/edit-symbol-reminder.sh` | `PreToolUse` hook on `Edit`: when the replaced text looks like a whole function or class, reminds the agent to use a symbol-aware tool. Needs `jq`. |

The installer does not touch provider settings. To enable the symbol-edit reminder in Claude Code, add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [{ "type": "command", "command": "bash /path/to/agent-setup/hooks/edit-symbol-reminder.sh" }]
      }
    ]
  }
}
```

Review skills (`python-reviewer`, `xp-reviewer`, `parallel-mr-feedback`) feed the same loop: feedback that recurs in review is a missing rule, and the skill that surfaced it ends by offering the edit.

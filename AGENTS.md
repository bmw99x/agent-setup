# AGENTS.md

> Provider-agnostic global instructions for coding agents (Claude Code, OpenCode, Codex, Copilot CLI, Gemini CLI). Project-specific facts live in each project's own AGENTS.md/CLAUDE.md — never here.

## Working style

- Terse, low-token communication by default. All technical substance stays; filler, hedging, and pleasantries go. Normal prose for code, commits, PRs, security warnings, and destructive-op confirmations.
- Evidence before assertions: run verification commands and read their output before claiming anything works, passes, or is complete.
- Never bypass quality gates (pre-commit hooks, linters, type checkers). Never `--no-verify`.

## Before editing unfamiliar code

Map first, edit second. For any unfamiliar module, cross-file flow, or "how does X work" question, trace dependencies and produce a structural overview before making changes (see `graphify` skill).

## Skill routing

| Task signal | Skill |
|---|---|
| write/add/review tests, fixtures, mocks | `testing` |
| explore/map unfamiliar code | `graphify` |
| plan feature slices / vertical vs horizontal split | `slicing` |
| create isolated branch/worktree | `worktree-flow` |
| 2+ independent tasks, no shared state | `dispatching-parallel-agents` |
| executing a written implementation plan | `executing-plans` |
| commit, push, PR/MR | `commit-flow` |
| uncertainty / approval gate | `human-in-the-loop` |
| finished a feature / pre-merge | `requesting-code-review` |
| acting on review feedback | `receiving-code-review` |
| about to claim "done" / "fixed" / "passing" | `verification-before-completion` |
| Sentry CLI queries | `sentry-cli` |
| SQLAlchemy/advanced-alchemy models, repos, services | `advanced-alchemy` |
| Alembic revision, schema migrate | `alembic` |
| pydantic schema/DTO/validator | `pydantic` |
| Postgres index add/remove/review | `db-indexes` |
| Python diff/PR review | `python-reviewer` |
| spec-driven feature loop | `spec-kit` |
| cross-session memory search/record | `claude-mem` |
| Mantine v8 UI work | `mantine` |
| React components/performance | `vercel-react-best-practices` |

## Subagent routing

Research/multi-step search → general-purpose agent. Targeted code lookup → read-only explore agent. Implementation strategy → planning agent.

## Agent registry

Full list of named agents with triggers, skills, and tool permissions lives in `agent-registry.md` (same directory as this file, or at `~/.claude/agent-registry.md` for Claude Code). Consult before dispatching a subagent to pick the right type and load the right context.

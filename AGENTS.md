# AGENTS.md

> Provider-agnostic global instructions for coding agents (Claude Code, OpenCode, Codex, Copilot CLI, Gemini CLI). Project-specific facts live in each project's own AGENTS.md/CLAUDE.md — never here.

## Tool priority: rtk > serena MCP > raw bash

**THIS IS MANDATORY. NEVER SKIP THIS. NO EXCEPTIONS.**

When you need to explore, search, read, diff, or run dev tools, you **MUST** prefer these in order:

### 1. rtk — available CLI proxy (token-optimized output)

`rtk` filters/compresses output before it reaches your context. Always prefer the `rtk` variant over the raw command:

| Instead of               | Use                       | Why                                             |
| ------------------------ | ------------------------- | ----------------------------------------------- |
| `ls`, `find`             | `rtk ls`, `rtk find`      | Strips noise, groups output                     |
| `cat`, `head`, `tail`    | `rtk read`                | Intelligent filtering                           |
| `grep`, `rg`             | `rtk grep`, `rtk rg`      | Whitespace stripping, truncation, file grouping |
| `git diff`, `git log`    | `rtk diff`, `rtk git log` | Only changed lines, dedup                       |
| `npm test`, `npx vitest` | `rtk test`, `rtk vitest`  | Only failures shown                             |
| `pnpm`, `npm`            | `rtk pnpm`                | Ultra-compact output                            |
| `npx tsc --noEmit`       | `rtk tsc`                 | Grouped errors                                  |

Full list: `rtk ls`, `rtk tree`, `rtk read`, `rtk smart`, `rtk git`, `rtk gh`, `rtk glab`, `rtk aws`, `rtk psql`, `rtk pnpm`, `rtk err`, `rtk test`, `rtk json`, `rtk deps`, `rtk env`, `rtk find`, `rtk diff`, `rtk log`, `rtk dotnet`, `rtk docker`, `rtk kubectl`, `rtk oc`, `rtk summary`, `rtk grep`, `rtk rg`, `rtk wget`, `rtk wc`, `rtk gain`, `rtk jest`, `rtk vitest`, `rtk prisma`, `rtk tsc`.

### 2. serena MCP — code-aware exploration and editing

serena understands code structure (symbol trees, references, types). Prefer serena over raw grep/sed/edit for code work:

| Instead of                      | Use                               | Why                               |
| ------------------------------- | --------------------------------- | --------------------------------- |
| `grep`/`rg` for symbols         | `serena_find_symbol`              | Finds declarations, not just text |
| `grep`/`rg` for text            | `serena_search_for_pattern`       | Code-aware search with context    |
| `sed`/`awk`/manual replace      | `serena_replace_in_files`         | Safe multi-file, dry-run first    |
| Reading a file to understand it | `serena_get_symbols_overview`     | Compact symbol table first        |
| Finding all callers/usages      | `serena_find_referencing_symbols` | Proper reference resolution       |
| "Where is X defined"            | `serena_find_declaration`         | Jump-to-definition                |
| New project setup               | `serena_initial_instructions`     | Read the manual                   |

### 3. raw bash — last resort

Only use raw bash (`ls`, `cat`, `grep`, `rg`, `find`, `sed`, `git diff`, `npm test`, etc.) when no `rtk` or serena equivalent exists. **When an `rtk` or serena tool CAN do the job, you MUST use it. Do not rationalize skipping this.**

- `rtk` is installed at `/opt/homebrew/bin/rtk`. Verify availability with `which rtk`.
- serena MCP tools are listed in your tool palette as `serena_*`.
- This applies to **exploration, searching, reading, diffing, running tests/lint/build** and any other command where `rtk` has a subcommand.

## Working style

- Terse, low-token communication by default. All technical substance stays; filler, hedging, and pleasantries go. Normal prose for code, commits, PRs, security warnings, and destructive-op confirmations.
- Evidence before assertions: run verification commands and read their output before claiming anything works, passes, or is complete.
- Never bypass quality gates (pre-commit hooks, linters, type checkers). Never `--no-verify`.

## Before editing unfamiliar code

Map first, edit second. For any unfamiliar module, cross-file flow, or "how does X work" question, trace dependencies and produce a structural overview before making changes (see `graphify` skill).

## Skill routing

General workflow skills (brainstorming, TDD, planning, debugging, subagent-driven development, code review, etc.) are provided by the [Superpowers v6+](https://github.com/obra/Superpowers) plugin — install per-provider.

| Task signal                                         | Skill                         |
| --------------------------------------------------- | ----------------------------- |
| write/add/review tests, fixtures, mocks             | `testing`                     |
| explore/map unfamiliar code                         | `graphify`                    |
| plan feature slices / vertical vs horizontal split  | `slicing`                     |
| create isolated branch/worktree                     | `worktree-flow`               |
| commit, push, PR/MR                                 | `commit-flow`                 |
| uncertainty / approval gate                         | `human-in-the-loop`           |
| Sentry CLI queries                                  | `sentry-cli`                  |
| SQLAlchemy/advanced-alchemy models, repos, services | `advanced-alchemy`            |
| Alembic revision, schema migrate                    | `alembic`                     |
| pydantic schema/DTO/validator                       | `pydantic`                    |
| Postgres index add/remove/review                    | `db-indexes`                  |
| Python diff/PR review                               | `python-reviewer`             |
| spec-driven feature loop                            | `spec-kit`                    |
| cross-session memory search/record                  | `claude-mem`                  |
| Mantine v8 UI work                                  | `mantine`                     |
| React components/performance                        | `vercel-react-best-practices` |

## Subagent routing

Research/multi-step search → general-purpose agent. Targeted code lookup → read-only explore agent. Implementation strategy → planning agent.

## Agent registry

Full list of named agents with triggers, skills, and tool permissions lives in `agent-registry.md` (same directory as this file, or at `~/.claude/agent-registry.md` for Claude Code). Consult before dispatching a subagent to pick the right type and load the right context.

---
name: sentry-cli
version: 0.34.0
description: Guide for using the new `sentry` CLI (cli.sentry.dev; not the legacy Rust `sentry-cli` binary) to interact with Sentry from the command line. Use when the user asks about viewing issues, events, projects, organizations, making API calls, or authenticating with Sentry via CLI.
requires:
  bins: ["sentry"]
  auth: true
---

# Sentry CLI Usage Guide

Help users interact with Sentry from the command line using the `sentry` CLI.

## Agent Guidance

Best practices and operational guidance for AI coding agents using the Sentry CLI.

### Key Principles

- **Just run the command** — the CLI handles authentication and org/project detection automatically. Don't pre-authenticate or look up org/project before running commands. If auth is needed, the CLI prompts interactively; in a non-interactive shell it exits 10–19 instead — ask the user to run `sentry auth login`.
- **Prefer CLI commands over raw API calls** — the CLI has dedicated commands for most tasks. Reach for `sentry issue view`, `sentry issue list`, `sentry trace view`, etc. before constructing API calls manually or fetching external documentation.
- **Use `sentry schema` to explore the API** — if you need to discover API endpoints, run `sentry schema` to browse interactively or `sentry schema <resource>` to search. This is faster than fetching OpenAPI specs externally.
- **Use `sentry issue view <id>` to investigate issues** — when asked about a specific issue (e.g., `CLI-G5`, `PROJECT-123`), use `sentry issue view` directly.
- **Use `--json` for machine-readable output** — pipe through `jq` for filtering. Human-readable output includes formatting that is hard to parse.
- **The CLI auto-detects org/project** — most commands work without explicit targets by checking `.sentryclirc` config files, scanning for DSNs in `.env` files and source code, and matching directory names. Only specify `<org>/<project>` when the CLI reports it can't detect the target or detects the wrong one.

### Design Principles

The `sentry` CLI follows conventions from well-known tools — if you're familiar with them, that knowledge transfers directly:

- **`gh` (GitHub CLI) conventions**: The `sentry` CLI uses the same `<noun> <verb>` command pattern (e.g., `sentry issue list`, `sentry org view`). Flags follow `gh` conventions: `--json` for machine-readable output, `--fields` to select specific fields, `-w`/`--web` to open in browser, `-q`/`--query` for filtering, `-n`/`--limit` for result count.
- **`sentry api` mimics `curl`**: The `sentry api` command provides direct API access with a `curl`-like interface — `--method` for HTTP method, `--data` for request body, `--header` for custom headers. It handles authentication automatically. If you know how to call a REST API with `curl`, the same patterns apply.

### Context Window Tips

- Use `--json --fields` to select specific fields and reduce output size. Run `<command> --help` to see available fields. Example: `sentry issue list --json --fields shortId,title,priority,level,status`
- Use `--json` when piping output between commands or processing programmatically
- Use `--limit` to cap the number of results (default is usually 10–100)
- Prefer `sentry issue view PROJECT-123` over listing and filtering manually
- Use `sentry api` for endpoints not covered by dedicated commands

### Safety Rules

- Always confirm with the user before running destructive or irreversible commands: `project delete`, `release delete`, `issue merge`, `trial start`, and any `sentry api` call with `--method DELETE`/`PUT`/`POST`
- For mutations, verify the org/project context looks correct in the command output before proceeding with further changes
- Never store or log authentication tokens — the CLI manages credentials automatically
- If the CLI reports the wrong org/project, override with explicit `<org>/<project>` arguments

### Exit Codes

The CLI uses semantic exit codes. Key ranges for agents:

| Range | Meaning | Agent Action |
|-------|---------|-------------|
| 0 | Success | Proceed normally |
| 10–19 | Auth error | Prompt user to run `sentry auth login` |
| 20–29 | Input error | Check command arguments and retry |
| 30–39 | API error | Retry or report to user |
| 40–49 | Feature unavailable | Inform user about plan/settings |
| 50–59 | Operation error | Report to user |
| 60–69 | Command-specific | Check stderr for details |

### Deeper guidance

- `references/workflows.md` — end-to-end recipes: investigate an issue, triage a release, trace a slow request, query the API directly
- Commands and flags: `sentry <noun> <verb> --help` and `sentry schema` are authoritative; `references/<noun>.md` (e.g. `issue.md`, `release.md`) has flags and examples per command group

## Prerequisites

The CLI must be installed and authenticated before use.

### Installation

```bash
curl https://cli.sentry.dev/install -fsS | bash
curl https://cli.sentry.dev/install -fsS | bash -s -- --version nightly

# Or install via npm/pnpm/bun
npm install -g sentry
```

### Authentication

```bash
sentry auth login
sentry auth login --token YOUR_SENTRY_API_TOKEN
sentry auth status
sentry auth logout
```

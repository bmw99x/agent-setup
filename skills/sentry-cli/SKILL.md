---
name: sentry-cli
version: 0.34.0
description: Guide for using the Sentry CLI to interact with Sentry from the command line. Use when the user asks about viewing issues, events, projects, organizations, making API calls, or authenticating with Sentry via CLI.
requires:
  bins: ["sentry"]
  auth: true
---

# Sentry CLI Usage Guide

Help users interact with Sentry from the command line using the `sentry` CLI.

## Agent Guidance

Best practices and operational guidance for AI coding agents using the Sentry CLI.

### Key Principles

- **Just run the command** — the CLI handles authentication and org/project detection automatically. Don't pre-authenticate or look up org/project before running commands. If auth is needed, the CLI prompts interactively.
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

- Always confirm with the user before running destructive commands: `project delete`, `trial start`
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

See [Exit Codes](/exit-codes/) for the complete reference.

### Deeper guidance

- `references/workflows.md` — end-to-end recipes: investigate an issue, triage a release, trace a slow request, query the API directly
- `references/dashboard-layout.md` — the 6-column grid, widget display types and sizing
- `references/quick-reference.md` — time filtering, output shaping, and the mistakes that bite most often

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

## Command Reference

### Auth

Authenticate with Sentry

- `sentry auth login` — Authenticate with Sentry
- `sentry auth logout` — Log out of Sentry
- `sentry auth refresh` — Refresh your authentication token
- `sentry auth status` — View authentication status
- `sentry auth token` — Print the stored authentication token
- `sentry auth whoami` — Show the currently authenticated identity

→ Full flags and examples: `references/auth.md`

### Org

Work with Sentry organizations

- `sentry org list` — List organizations
- `sentry org view <org>` — View details of an organization

→ Full flags and examples: `references/org.md`

### Project

Work with Sentry projects

- `sentry project create <name> <platform>` — Create a new project
- `sentry project delete <org/project>` — Delete a project
- `sentry project list <org/project>` — List projects
- `sentry project view <org/project>` — View details of a project

→ Full flags and examples: `references/project.md`

### Issue

Manage Sentry issues

- `sentry issue list <org/project>` — List issues in a project
- `sentry issue events <issue>` — List events for a specific issue
- `sentry issue explain <issue>` — Analyze an issue's root cause using Seer AI
- `sentry issue plan <issue>` — Generate a solution plan using Seer AI
- `sentry issue view <issue>` — View details of a specific issue
- `sentry issue resolve <issue>` — Mark an issue as resolved
- `sentry issue unresolve <issue>` — Reopen a resolved issue
- `sentry issue archive <issue>` — Archive (ignore) an issue
- `sentry issue merge <issue...>` — Merge 2+ issues into a single canonical group

→ Full flags and examples: `references/issue.md`

### Event

View and list Sentry events

- `sentry event view <org/project/event-id...>` — View details of one or more events
- `sentry event list <issue>` — List events for an issue

→ Full flags and examples: `references/event.md`

### API

Make an authenticated API request

- `sentry api <endpoint>` — Make an authenticated API request

→ Full flags and examples: `references/api.md`

### CLI

CLI-related commands

- `sentry cli defaults <key value...>` — View and manage default settings
- `sentry cli feedback <message...>` — Send feedback about the CLI
- `sentry cli fix` — Diagnose and repair CLI database issues
- `sentry cli setup` — Configure shell integration
- `sentry cli upgrade <version>` — Update the Sentry CLI to the latest version

→ Full flags and examples: `references/cli.md`

### Dashboard

Manage Sentry dashboards

- `sentry dashboard list <org/title-filter...>` — List dashboards
- `sentry dashboard view <org/project/dashboard...>` — View a dashboard
- `sentry dashboard create <org/project/title...>` — Create a dashboard
- `sentry dashboard widget add <org/project/dashboard/title...>` — Add a widget to a dashboard
- `sentry dashboard widget edit <org/project/dashboard...>` — Edit a widget in a dashboard
- `sentry dashboard widget delete <org/project/dashboard...>` — Delete a widget from a dashboard
- `sentry dashboard revisions <org/dashboard...>` — List dashboard revisions
- `sentry dashboard restore <org/dashboard...>` — Restore a dashboard revision

→ Full flags and examples: `references/dashboard.md`

### Replay

Search and inspect Session Replays

- `sentry replay list <org/project>` — List recent Session Replays
- `sentry replay view <replay-id-or-url...>` — View a Session Replay

→ Full flags and examples: `references/replay.md`

### Release

Work with Sentry releases

- `sentry release list <org/project>` — List releases with adoption and health metrics
- `sentry release view <org/version...>` — View release details with health metrics
- `sentry release create <org/version...>` — Create a release
- `sentry release finalize <org/version...>` — Finalize a release
- `sentry release delete <org/version...>` — Delete a release
- `sentry release deploy <org/version environment name...>` — Create a deploy for a release
- `sentry release deploys <org/version...>` — List deploys for a release
- `sentry release set-commits <org/version...>` — Set commits for a release
- `sentry release propose-version` — Propose a release version

→ Full flags and examples: `references/release.md`

### Repo

Work with Sentry repositories

- `sentry repo list <org/project>` — List repositories

→ Full flags and examples: `references/repo.md`

### Team

Work with Sentry teams

- `sentry team list <org/project>` — List teams

→ Full flags and examples: `references/team.md`

### Explore

Query aggregate event data (Explore)

- `sentry explore <target>` — Query aggregate event data (Explore)

→ Full flags and examples: `references/explore.md`

### Log

View Sentry logs

- `sentry log list <org/project-or-trace-id...>` — List logs from a project
- `sentry log view <org/project/log-id...>` — View details of one or more log entries

→ Full flags and examples: `references/log.md`

### Sourcemap

Manage sourcemaps

- `sentry sourcemap inject <directory>` — Inject debug IDs into JavaScript files and sourcemaps
- `sentry sourcemap upload <directory>` — Upload sourcemaps to Sentry

→ Full flags and examples: `references/sourcemap.md`

### Span

List and view spans in projects or traces

- `sentry span list <org/project/trace-id...>` — List spans in a project or trace
- `sentry span view <trace-id/span-id...>` — View details of specific spans

→ Full flags and examples: `references/span.md`

### Trace

View distributed traces

- `sentry trace list <org/project>` — List recent traces in a project
- `sentry trace view <org/project/trace-id...>` — View details of a specific trace
- `sentry trace logs <org/project/trace-id...>` — View logs associated with a trace

→ Full flags and examples: `references/trace.md`

### Trial

Manage product trials

- `sentry trial list <org>` — List product trials
- `sentry trial start <name> <org>` — Start a product trial

→ Full flags and examples: `references/trial.md`

### Init

Initialize Sentry in your project (experimental)

- `sentry init <target> <directory>` — Initialize Sentry in your project (experimental)

→ Full flags and examples: `references/init.md`

### Schema

Browse the Sentry API schema

- `sentry schema <resource...>` — Browse the Sentry API schema

→ Full flags and examples: `references/schema.md`

## Global Options

All commands support the following global options:

- `--help` - Show help for the command
- `--version` - Show CLI version
- `--log-level <level>` - Set log verbosity (`error`, `warn`, `log`, `info`, `debug`, `trace`). Overrides `SENTRY_LOG_LEVEL`
- `--verbose` - Shorthand for `--log-level debug`

## Output Formats

### JSON Output

Most list and view commands support `--json` flag for JSON output, making it easy to integrate with other tools:

```bash
sentry org list --json | jq '.[] | .slug'
```

### Opening in Browser

View commands support `-w` or `--web` flag to open the resource in your browser:

```bash
sentry issue view PROJ-123 -w
```

# Quick Reference

## Time filtering

Use `--period` (alias: `-t`) to filter by time window:

```bash
sentry trace list --period 1h
sentry span list --period 24h
sentry span list -t 7d
```

## Scoping to an org or project

Org and project are positional arguments following `gh` CLI conventions:

```bash
sentry trace list my-org/my-project
sentry issue list my-org/my-project
sentry span list my-org/my-project/abc123def456...
```

## Listing spans in a trace

Pass the trace ID as a positional argument to `span list`:

```bash
sentry span list abc123def456...
sentry span list my-org/my-project/abc123def456...
```

## Dataset names for the Events API

When querying the Events API (directly or via `sentry api`), valid dataset values are: `spans`, `transactions`, `logs`, `errors`, `discover`.

## Common Mistakes

- **Wrong issue ID format**: Use `PROJECT-123` (short ID), not the numeric ID `123456789`. The short ID includes the project prefix.
- **Pre-authenticating unnecessarily**: Don't run `sentry auth login` before every command. The CLI detects missing/expired auth and prompts automatically. Only run `sentry auth login` if you need to switch accounts.
- **Missing `--json` for piping**: Human-readable output includes formatting. Use `--json` when parsing output programmatically.
- **Specifying org/project when not needed**: Auto-detection resolves org/project from `.sentryclirc` config files, DSNs, env vars, and directory names. Let it work first — only add `<org>/<project>` if the CLI says it can't detect the target or detects the wrong one.
- **Confusing `--query` syntax**: The `--query` flag uses Sentry search syntax (e.g., `is:unresolved`, `assigned:me`), not free text search.
- **Not using `--web`**: View commands support `-w`/`--web` to open the resource in the browser — useful for sharing links.
- **Fetching API schemas instead of using the CLI**: Prefer `sentry schema` to browse the API and `sentry api` to make requests — the CLI handles authentication and endpoint resolution, so there's rarely a need to download OpenAPI specs separately.
- **Release version mismatch**: The `org/version` positional is `<org-slug>/<version>`, where `org/` is the org, not part of the version. `sentry release create sentry/1.0.0` creates version `1.0.0` in org `sentry`. If your `Sentry.init()` uses `release: "1.0.0"`, this is correct. Don't double-prefix like `sentry/myapp/1.0.0`.
- **Running `set-commits --auto` without a git checkout**: `--auto` needs a local git repo to discover the origin remote URL and HEAD commit. In CI, ensure `actions/checkout` with `fetch-depth: 0` runs before `set-commits --auto`.
- **Using `sentry api` when CLI commands suffice**: `sentry issue list --json` already includes `shortId`, `title`, `priority`, `level`, `status`, `permalink`, and other fields at the top level. Some fields like `count`, `userCount`, `firstSeen`, and `lastSeen` may be null depending on the issue. Use `--fields` to select specific fields and `--help` to see all available fields. Only fall back to `sentry api` for data the CLI doesn't expose.

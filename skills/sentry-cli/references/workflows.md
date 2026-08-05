# Workflow Patterns

## Investigate an Issue

```bash
# 1. Find the issue (auto-detects org/project from DSN or config)
sentry issue list --query "is:unresolved" --limit 5

# 2. Get details
sentry issue view PROJECT-123

# 3. Get AI root cause analysis
sentry issue explain PROJECT-123

# 4. Get a fix plan
sentry issue plan PROJECT-123
```

## Explore Traces and Performance

```bash
# 1. List recent traces (auto-detects org/project)
sentry trace list --limit 5

# 2. View a specific trace with span tree
sentry trace view abc123def456...

# 3. View spans for a trace
sentry span list abc123def456...

# 4. View logs associated with a trace
sentry trace logs abc123def456...
```

## Stream Logs

```bash
# Stream logs in real-time (auto-detects org/project)
sentry log list --follow

# Filter logs by severity
sentry log list --query "severity:error"
```

## Explore the API Schema

```bash
# Browse all API resource categories
sentry schema

# Search for endpoints related to a resource
sentry schema issues

# Get details about a specific endpoint
sentry schema "GET /api/0/organizations/{organization_id_or_slug}/issues/"
```

## Manage Releases

```bash
# Create a release — version must match Sentry.init({ release }) exactly
sentry release create my-org/1.0.0 --project my-project

# Associate commits via repository integration (needs local git checkout)
sentry release set-commits my-org/1.0.0 --auto

# Or read commits from local git history (no integration needed)
sentry release set-commits my-org/1.0.0 --local

# Mark the release as finalized
sentry release finalize my-org/1.0.0

# Record a production deploy
sentry release deploy my-org/1.0.0 production
```

**Key details:**
- The positional is `<org-slug>/<version>`. In `sentry release create sentry/1.0.0`, `sentry` is the org and `1.0.0` is the version — the slash separates org from version, it is not part of the version string.
- The **version** must match the `release` value in `Sentry.init()`. If your SDK uses `"1.0.0"`, the command must use `org/1.0.0`.
- `--auto` requires a Sentry repository integration (GitHub/GitLab/Bitbucket) **and** a local git checkout. It matches your `origin` remote against Sentry's repo list. Without a checkout, use `--local`.
- With no flag, `set-commits` tries `--auto` first and falls back to `--local` on failure.

## Arbitrary API Access

```bash
# GET request (default)
sentry api /api/0/organizations/my-org/

# POST request with data
sentry api /api/0/organizations/my-org/projects/ --method POST --data '{"name":"new-project","platform":"python"}'
```

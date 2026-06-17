---
name: commit-flow
description: Use when staging changes, writing commits, pushing branches, or opening PRs/MRs.
---

# commit-flow

## Gates

- Never bypass hooks (`--no-verify`, skip flags, disabled checks) unless user explicitly approves.
- Explicit staging only. Avoid `git add -A` / `git add .` unless repo is intentionally all yours.
- Inspect staged diff and branch diff before push.
- Secret scan staged files + branch diff, including HTTP files, docs, fixtures, examples.
- Run quick local lint/type/format checks when relevant.
- Behavior change → targeted tests.
- Large branch → full tests or local CI-equivalent.
- DB model/migration/seed → migration consistency check, migrate up/down where supported, relevant DB tests.
- Tiny non-risky change after same-branch green CI may skip extra tests; state why in PR/MR test plan.

CI confirms. Local gate catches iteration failures.

## Secrets

- Exclude env files, caches, sensitive CSVs/data.
- HTTP/client files may be committed only with placeholders: `{{API_KEY}}`, `{{BASE_URL}}`, `{{RESOURCE_ID}}`.
- Never commit API keys, bearer tokens, cookies, signed URLs, secrets.
- If secret pushed: rotate/revoke first. History rewrite only with explicit approval; it can damage branch stacks.

## Commit Message

```text
<type>[optional scope]: <description>

[optional body: why]

[optional issue/task reference]
```

Rules:
- Prefer Conventional Commits when project has no other convention.
- Common types: `build`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`, `test`, `chore`.
- Scope = subsystem/package when useful.
- Subject concise, imperative, no trailing period.
- No AI co-author/footer unless user/project requires it.

## Hook Failure

Hook failed → fix root cause → stage explicit files → new commit. Do not amend failed commit unless user asked.

## PR/MR

- Target default branch by default.
- Remote stacked PR/MR only if user approved stack/integration branch.
- If locally stacked: rebase onto default/foundation, verify independent diff, then create PR/MR.
- Body: summary, test evidence, risks, linked task/issue, agent decisions/open questions if any.
- Merge: follow project strategy. Avoid merge commits unless project uses them.

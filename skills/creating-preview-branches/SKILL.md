---
name: creating-preview-branches
description: Use when creating, spinning up, or deploying a preview environment for changes across geobe-api, gim, shiva, geo, or geo-porter — triggers on "create a preview for these changes", "spin up a preview", "preview branch", "preview environment", "deploy a preview". Covers per-service branch selection and MR setup in the preview-branches repo.
---

# creating-preview-branches

Trigger: "create a preview for these changes", "spin up a preview", "deploy a preview branch", "preview environment".

## Overview

`preview-branches` is a pure orchestrator repo — deploys a multi-service env per MR at
`geo-mr-<IID>.preview.misgeo.io`, assembled from pre-built images in each service's own
registry. Services: `geobe-api`, `gim`, `shiva`, `geo`, `geo-porter`.

## Workflow

1. **Ask which branch each service should deploy.** Ask once, covering all 5 services,
   default `main` for any not answered. Don't assume — the requesting change may span
   several services with different in-flight branches.
2. **Verify images exist for non-`main` branches** — resolution is strict for named
   branches: `latest-<branch-slug>` (slashes → dashes) must already exist in that
   service's registry, or CI fails rather than falling back. If a branch hasn't built
   yet, tell the user to push it first (or wait for its pipeline).
3. **Write `.preview.yml`** at the repo root of the `preview-branches` MR branch:
   ```yaml
   services:
     geobe-api: feature/new-claims-api
     gim: main
     # omit a service entirely to auto-match branch-name, then main
   ```
   Omit services the user pinned to `main` — they fall back there anyway.
4. **Open the MR** — REQUIRED SUB-SKILL: use `creating-merge-requests` for body/ClickUp/diagram
   conventions. Target the default branch. Name the source branch after the feature.
5. **Add the `preview` label** — the pipeline only runs with it:
   `glab mr create ... --label preview` (or `glab mr update <IID> --label preview` if
   already open).
6. **Report the URL** once the pipeline succeeds: `https://geo-mr-<IID>.preview.misgeo.io`.
   GitLab Operations → Environments also lists it.

## Resolution precedence (per service, first match wins)

| # | Source | Strict? |
|---|---|---|
| 1 | `<SERVICE>_TAG` pipeline variable | yes |
| 2 | `services.<name>` in `.preview.yml` | yes |
| 3 | `latest-<MR branch name>` (auto-match) | lenient — falls back silently |
| 4 | `latest-main` | lenient |

Strict = named branch with no image → CI fails. Lenient = auto-match quietly falls back
to `main`; that's by design, not a bug.

## Other operations

- **Re-deploy:** retry the pipeline, or push a new commit to the MR branch.
- **Tear down:** MR widget or Operations → Environments → `teardown:destroy` (manual job).
- **QA:** pass/fail via `qa::pass` / `qa::fail` MR labels; notifications land in
  ClickUp + Slack.

## Common mistakes

- Naming a branch with no built image → CI fails instead of deploying `main`. Check the
  service's registry first, or leave it unpinned to auto-match/fall back.
- Forgetting the `preview` label → pipeline never runs.
- Pinning a service to `main` explicitly in `.preview.yml` — harmless but redundant, omit
  instead.

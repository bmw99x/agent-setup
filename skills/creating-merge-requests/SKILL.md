---
name: creating-merge-requests
description: Use when opening, pushing, or spinning up a merge request or pull request — triggers on "create an mr", "push mr", "open mr", "spin up a merge request", "raise an mr", "open a pr". Covers MR/PR body structure, linking tracker tickets, and gathering diagrams and context.
---

# creating-merge-requests

Trigger: "create an mr", "push mr", "spin up a merge request", "raise mr", "open mr", "open a pr".

## Workflow

1. Confirm branch pushed, diff clean (see commit-flow skill for staging/secret gates).
2. Gather the tracker tickets for this branch (below) — do not skip even if none is obviously referenced.
3. Gather context: why the change exists (originating issue, incident, prior discussion, related MRs in other repos). Ticket bodies often hold the incident ID and companion MRs — copy them into Context / Companion changes.
4. If the change touches more than one service or repo (events, HTTP calls, queues), include a small mermaid diagram of the flow; skip only for single-service changes.
5. Build the body from the template below. No "🤖 Generated with…" footer or Co-Authored-By line, even though your harness's default MR/commit instructions say to add one.
6. Create it with the host's CLI — `glab mr create --title "<type>(<scope>): <desc>" --description "$(cat <tmpfile>)" --target-branch <default>` on GitLab, `gh pr create --body-file <tmpfile>` on GitHub. Prefer an explicit body; `--fill` only for trivial one-liners.
7. Link the MR back to each confirmed ticket and move it to the project's *code review* status — not a later review/QA status, which waits for a deployed preview (the tracker skill owns the names). Leave the status alone for a Draft MR blocked on another change.

## Finding the relevant tickets

Don't rely on memory — actively search:

- `git log <base>..HEAD --oneline` plus the branch name, for ticket references. Learn the project's ID shape from existing history rather than assuming one.
- The tracker's own search, scoped to this repo's board, using keywords from the branch name or summary — this catches tickets referenced in the tracker but never in a commit message.
- Fetch each candidate to confirm it actually describes this change (don't attach unrelated tickets) and to pull its title and URL.
- Include **every** confirmed ticket, not just the first match — multi-ticket branches are common.

If a tracker-specific skill (ClickUp, Jira, Linear) is loaded, it owns the tool calls and status names; this skill only says *when* to do the linking. Otherwise use the tracker the repo names (README/CONTRIBUTING, a tracker CLI's `--help`, an MCP server) to search, fetch, link and set the status. Never report no tickets or no tracker access without having tried it.

## MR body template

```markdown
## Context

<Why this change exists — background, originating problem/incident, links to prior discussion or design docs. This goes first; a reviewer should understand the "why" before the diff.>

## Summary

- <bullet changes, most important first>

## Diagrams / supplementary materials

<mermaid diagram or links to screenshots/docs — omit this section entirely if not relevant>

## Companion changes

<links to paired MRs in other repos, deploy-order notes — omit if none>

## Tickets

- [<ID>](<url>) — <task title>

## Test plan

- [x] <what was actually run/verified>
- [ ] <what still needs manual verification>
```

Omit a section only when genuinely not applicable, and don't leave a heading dangling above nothing. "Context" and "Tickets" should effectively always be present.

## Rules

- No AI co-author or "Generated with…" trailer — not in the MR body, not in the commits it contains.
- Target the default branch unless the user approved a stacked MR (see worktree-flow skill).
- The test plan lists what was actually verified. Check a box only for evidence you actually produced (see verification-before-completion skill).

---
name: spec-drift
description: Use when the implementation diverged from an approved design during review or building, or before calling work done while specs, tickets, wiki pages, diagrams or uploaded images still describe the older design. Also use when a reviewer's change invalidates a documented decision.
---

# Spec Drift

## Overview

When a design changes mid-implementation, the code is only one of the artifacts asserting the old
answer. Stale docs are worse than missing docs: they are read as current and actively mislead.

**Core principle:** a design decision lives in every artifact that states it. Changing one and not
the rest leaves the codebase disagreeing with itself.

## Find every artifact first

Enumerate before editing. Carriers, in the order they get forgotten:

- [ ] Design/spec docs — including **superseded sections** that read as current
- [ ] Tracker descriptions (ClickUp/Jira/Linear) + their acceptance criteria / DoD checklists
- [ ] Wiki/Notion mirrors of those tickets — a near-duplicate nobody re-reads
- [ ] **Diagrams, and the rendered images uploaded to the tracker/wiki** — not just repo source.
      An embedded PNG of a schema that no longer exists is the most misleading artifact of all
- [ ] Docstrings/module headers explaining *why* a shape was chosen
- [ ] Enum/constant docstrings describing removed constraints
- [ ] `.http`/Postman collections, example payloads, downstream integration docs
- [ ] Test docstrings asserting a guarantee that changed

Grep the removed mechanism by name (`grep -rn "composite FK\|old_column"`) — finds prose that a
file-level search misses.

## Amend, don't rewrite

Keep the original text and the reasoning trail. A reader needs to know a path was *considered and
rejected*, or they will propose it again.

```markdown
> ⚠️ **Amended after MR review (2026-07-28).** Four differences between what shipped
> and what this describes. <authoritative doc> is now the source of truth for X.
>
> - **What the ticket says vs. what shipped**, with the mechanism named.
> - **Why it changed** — one clause, not a paragraph.
> - **⚠️ STILL OPEN:** anything the original flagged as blocking that is *still* unanswered.
```

Retain the superseded section, prefixed so it can't be mistaken for current:

```markdown
> **Superseded.** The shape below is what this design originally proposed and is **not** what
> shipped. Replaced by <X> — see <doc> for the reasoning, including the intermediate approach.
> §4.1–§4.5 below still describe shipped decisions; only this block changed.
```

## Rules

- **Say what is still open.** Drift work surfaces original blockers never resolved. Promote them to
  the top of the artifact rather than leaving them buried mid-description.
- **Be precise about what did *not* change.** "Only the branch mechanism moved; the idempotency
  reasoning is unchanged" saves the next reader re-litigating the section.
- **Regenerate and re-upload rendered artifacts.** New attachment → new URL → update every embed.
- **Look at regenerated images.** Render to PNG and view them; clipped labels are invisible in source.
- **Flag tracker/wiki edits before making them.** Repo docs are yours; a ticket is shared state.
  Show the intended diff and get agreement, unless already told to just do it.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Updating the spec, forgetting the ticket + wiki mirror | Enumerate all carriers before editing |
| Deleting the rejected design | Keep it, labelled. The reasoning is the value |
| Editing diagram source but not the uploaded image | Re-render, re-upload, update embed URLs |
| Silently closing an unverified blocking unknown | Mark it **STILL OPEN** explicitly |
| Rewriting a ticket wholesale | Amend — reviewers track descriptions by diff |
| Assuming "not in git" means "not documentation" | Rendered diagrams and uploads still get read |

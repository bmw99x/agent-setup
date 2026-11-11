---
name: session-housekeeping
description: Use when a long exploratory session is ending and the user wants a fresh session to continue without inheriting its bias — "housekeeping", "start fresh", "context is polluted", "record what we explored", "decision log", "what did we rule out and why", or "handoff without rubber-stamping". Not for resuming an in-flight task exactly where it stopped (session-handoff) or retrospectives on how Claude worked (session-meditate).
---

# Session Housekeeping

## Overview

Turns a polluted session into two files: a **journal** for the human (full story) and a **brief** for the next agent (distilled, neutral). The next session loads only the brief.

**Core principle:** the brief carries facts and their provenance, never direction. A fresh agent should be able to disagree with everything the old session concluded, but should never have to re-run its experiments.

## Output

`<project>/.claude/housekeeping/<YYYY-MM-DD>-<slug>/`
- `journal.md` — fill [references/journal-template.md](references/journal-template.md)
- `brief.md` — fill [references/brief-template.md](references/brief-template.md), ≤400 words (cell text counts, table pipes don't)

If an earlier brief exists in `.claude/housekeeping/`, read it; the new brief supersedes it and names it in its header.

## Steps

1. **Gather.** Walk the whole conversation. If it was compacted, recover early turns from the newest transcript in `~/.claude/projects/<cwd-slug>/*.jsonl` (user messages and tool results only).
2. **Classify every item** by its final status, using exactly one of these:
   - `measured` — a tool result, benchmark, or prototype exists, or the user reported running one (tag it `user-reported`). Record the number, dataset and environment.
   - `user-decided` — the user said yes or no. Quote them.
   - `claimed` — Claude asserted it with no tool output, however confident it sounded.
   - `parked` — deferred for time or priority.
   - `unexplored` — an adjacent option nobody tried.
3. **Write the journal**, then **distil the brief from it**. Each brief row gives what happened, the number, and its source, and ranks nothing.
   Each `Reopen if` names something a reader could check: a threshold (`live p95 > target on prod data`) or an event (`contract allows ±1%`).
4. **Cold-read check.** Give a fresh subagent only `brief.md` and ask: "List what is settled, what is open, and what you would question first." If it treats a `claimed` or `parked` item as settled, or names the old path as the default, reword that row and check once more.
5. **Publish the journal** as a private Artifact (load artifact-design first). The brief stays as markdown.
6. **Report:** both paths, the Artifact link, and the kickoff line for the new session:
   > Read `.claude/housekeeping/<dir>/brief.md`. Treat measured rows as facts and everything else as open. Do not read journal.md unless I ask.

Committing is the user's call.

## Common Mistakes

| Mistake | Fix |
|---|---|
| `Reopen if: revisited` / `time allows` | Name the threshold or the event. |
| Preference rejections look like evidence rejections | Fill the `Settled by` column. |
| Claude opinion recorded as a finding | Mark it `claimed` and list it under Untested claims. |
| Next steps or best approach in the brief | Rephrase as an Open question. |
| One-environment number stated as general | Put dataset and env in the Scope column. |

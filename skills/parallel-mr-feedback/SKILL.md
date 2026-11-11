---
name: parallel-mr-feedback
description: Use when asked to address, resolve, tackle, fix or work through review comments, threads or feedback on an MR/PR — especially "in parallel", "with agents" or "with subagents" — or via /parallel-mr-feedback <MR>. Fetches unresolved threads, groups them by file ownership, picks a model per group (haiku mechanical, sonnet domain/design, opus I/O/performance/orchestration), runs one worktree-isolated agent per group, integrates in dependency order, verifies, pushes, replies per thread, then prompts the user to turn the feedback into skill updates. Works on GitHub and GitLab. Accepts an MR/PR number or URL.
hooks:
  Stop:
    - hooks:
        - type: command
          command: "~/.claude/skills/parallel-mr-feedback/skill-update-reminder.sh"
---

# Parallel MR Feedback

One invocation clears an MR's open review threads with parallel agents, then harvests the feedback
into skills. Forge commands live in `references/forge.md`; the per-agent rules template is
`references/agent-rules.md`. Load both when you reach the step that needs them.

Reviewer threads are suggestions to evaluate, not orders: apply `superpowers:receiving-code-review`
judgement. A thread an agent declines with a reason is a valid outcome.

## Narration

Before each step, one line: `[mr-feedback] step <n> — <what and why>`.

## 1. Resolve the MR and fetch threads

Number or URL from the arguments, else the current branch's MR. Merged/closed or none found: say so
and stop. Record number, source branch, head SHA, base.

Write unresolved threads to `$SCRATCH/threads.txt`, one per line:
`[thread-id] path:line :: text` (`references/forge.md`). Line numbers refer to the commented head,
so agents locate code by content. Zero threads: say so and stop (skip step 11's prompt only then).

## 2. Group by file ownership

Cluster threads so that no two groups edit the same file. That is the hard constraint — parallel
agents must never touch the same file. Threads on one file, or on files that must change together,
go in one group. Then order the groups into waves:

1. **Foundation** — a cross-cutting abstraction the others consume (a caching module, a proxy
   service, a shared DTO). Runs alone, first.
2. **Per-file refactors** — independent groups, run in parallel on top of the foundation.
3. **Sweep** — repo-wide mechanical changes (rename, comment removal, import moves). Last, so it
   does not conflict with the refactors.

Show the user the groups, waves and models in a short table and continue unless they object.

## 3. Pick the model per group

| Work | Model |
|---|---|
| Simple code, moves, mechanical refactors, renames, comment/docstring fixes | `haiku` |
| Domain-level concerns, tech debt, design patterns, naming in the domain language | `sonnet` |
| I/O, performance, orchestration, complex abstractions, anything the foundation wave builds | `opus` |

A group mixing tiers takes the highest tier in it. When unsure between two, take the higher.

## 4. Isolate

Per group, from the MR head SHA:

```bash
git worktree add ../<repo>-mrfb-<group> -b mrfb/<group> <head-sha>
```

Later waves branch from the integrated result of the earlier waves, not the original head.
Write the shared rules file from `references/agent-rules.md` to scratch, filled in for the repo.

## 5. Brief and dispatch

One agent per group, same wave in a single message so they run concurrently, `model` set per
step 3. Each brief contains: worktree path and branch, the thread lines for that group (copied
from `threads.txt`), the files it owns, the goal in a sentence per thread, and the path to the
rules file. Require a report with one entry per thread id. Do not paste the diff or code; agents
read the worktree.

## 6. Integrate

In wave and dependency order, for each finished branch:

1. Read its report. Every thread id needs an entry; missing ids go back to the agent.
2. `git rebase <mr-branch>` the agent branch, resolve conflicts, run the full suite.
3. Green: fast-forward the MR branch. Red: fix it, or send it back. Never merge red.

Start the next wave's worktrees only after the previous wave is merged.

## 7. Verify before trusting

Re-run the gates yourself on the final branch: linters, type checker, full suite. Agent reports
are claims; the suite output is evidence. Skim each diff against its thread. If an agent ran while
a safety classifier or permission checker was unavailable, review its diff in full.

## 8. Push

Push the MR branch. Branches stacked on it need a rebase and `--force-with-lease`; never plain
force. No `--no-verify`.

## 9. Reply per thread

For each thread: a reply with the commit SHA and what changed, or the reason it was declined
(`references/forge.md`). Do not resolve threads; the reviewer does.

## 10. Clean up

Remove the worktrees and `mrfb/*` branches once merged and pushed.

## 11. Prompt for skill updates — mandatory

Last step of every run. Stop-hook reminders fire if this is skipped, but do it here. Ask the user
whether to turn this MR's feedback into skill edits, and offer a concrete list drawn from the
threads, not a generic question. Reviewer feedback that recurs is a missing rule.

Classify each proposal by scope and kind:

- **Scope:** repo (`.claude/skills/` in the repo) or global (`agent-setup` skills, `~/.claude/skills`).
- **Kind:** language idiom, repo-specific convention, domain, SOLID, design pattern, org convention.

Format: `<scope> / <kind> — <skill to create or edit> — <one-line rule> — (threads: <ids>)`.
Prefer editing an existing skill over creating one. Offer only; apply nothing until the user picks.

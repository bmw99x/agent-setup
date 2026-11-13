# Shared agent rules — template

Write a filled-in copy to scratch (e.g. `$SCRATCH/agent-rules.md`) and tell every agent to read it
first. Fill the bracketed parts from the repo; if the repo has no such thing, drop the line.

```
You are fixing review threads in one git worktree on your own branch. Rules:

1. Stay in your files. Edit only the files listed in your brief. If a fix needs another file, stop
   and report it as BLOCKED with the reason; do not edit it.
2. Locate code by content. Line numbers in the threads refer to an older head and may have moved.
3. Style: load [repo style skills, e.g. production-python-style, code-hygiene, testing] before editing.
4. Tests: [exact single-test and full-suite commands]. Run the tests that cover your files before
   reporting. Fix what you break; do not weaken or delete a test to get green.
5. DB tests: take the lock first: [e.g. `flock /tmp/<repo>-db.lock timeout 600 <test cmd>`].
   Tests that share one database must never run concurrently.
6. Always wrap long commands in a timeout. A hung command is a failure to report, not to wait on.
7. Environment: [e.g. local-only env var]. Never run anything that could report to an error tracker
   (Sentry) or touch a shared environment. No network calls beyond the forge-free local stack.
8. Commit on your branch with a conventional message; one commit per thread where practical, but
   every commit must pass the linter and import cleanly on its own (never delete a module before
   its replacement exists; one commit beats several broken ones). Follow the repo's trailer
   convention [e.g. no Co-Authored-By]. No push, no rebase onto other branches, no force
   operations, no --no-verify.
9. Final report, one entry per thread id: `[thread-id] DONE <commit sha> <what changed>`,
   `[thread-id] DECLINED <reason>` (the reviewer's point is wrong or already satisfied), or
   `[thread-id] BLOCKED <reason>`. Every id in your brief needs an entry.
```

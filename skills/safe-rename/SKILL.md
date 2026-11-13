---
name: safe-rename
description: "Use for any rename of a function, class, field, flag or term across a codebase ('rename X to Y', finishing a half-done rename) - especially when the old name is a substring of other identifiers (test names, fixtures, docs) or a green suite could hide leftovers. Ensures every reference is renamed and verified, not only exact matches."
---

# Safe Rename

## Overview

The risky part of a cross-file rename is not the replacing — it is **proving nothing silently
disappeared**. A rename can remove tests from collection while the suite still reports green, because
a test function whose name no longer starts with `test_` is not failed, it is simply never run.

**Core principle:** a green suite after a rename proves the tests that ran passed. It does not prove
the same tests ran.

> Scoping note: this skill deliberately does **not** lecture on word boundaries. Baseline testing
> showed agents handle the mechanics correctly — using `\b` anchors, spotting the substring trap
> unprompted. The gap was verification: neither baseline confirmed via the test runner. That is what
> this skill covers.

## Prefer a symbol-aware rename

Reach for the tool that understands the language first — `mcp__serena__rename_symbol`, IDE/LSP
rename, `rope`, `gopls`. Text substitution is the fallback for docstrings, comments, and prose the
symbol tool won't touch. It also skips identifiers that *contain* the name (`test_old_name_*`,
fixtures): rename those that are about this symbol by hand.

## The verification contract

Run all four. The count comparison is the one that catches silent loss.

```bash
# 1. BEFORE — record the collection count (unrecoverable afterwards)
pytest --collect-only -q | tail -1        # e.g. "247 tests collected"

# 2. AFTER — must match, or the delta must be one you can explain
pytest --collect-only -q | tail -1

# 3. No identifier glued together by a substring replace
grep -rnE "[a-zA-Z]new_name|new_name[a-zA-Z]" --include=*.py .

# 4. No stragglers, in code OR prose
grep -rn "old_name" --include=*.py --include=*.md .
```

Every hit left by check 4 must be an unrelated identifier that merely contains `old_name` (leave
it) or a deliberately kept name such as a task entrypoint (say so). Anything else is a straggler.

A dropped count with a green suite is the exact failure this exists for: the tests were not
renamed-and-broken, they were renamed-and-uncollected.

## Read the raw output

Compact/wrapping reporters summarise. Redirect and read the real thing, then confirm the renamed
tests appear by name:

```bash
pytest -q > /tmp/after.txt 2>&1; tail -20 /tmp/after.txt
pytest path/to/test_file.py -v | grep new_name
```

## Quick Reference

| Check | Catches |
|---|---|
| Collection count before/after | Tests silently dropped from collection |
| Glued-identifier grep | `test_` prefix eaten by a substring replace |
| Straggler grep incl. `.md` | Stale docs, docstrings, spec references |
| Named-test verbose run | "It passed" vs. "it ran" |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Trusting "N passed" from a summarising reporter | Redirect to a file and read the tail |
| Never establishing a before-count | Capture `--collect-only` *first*; afterwards it is unrecoverable |
| Running tests concurrently with another suite | Shared test DBs collide (`AdminShutdown`, dropped-database errors). Check for other runners first |
| Grepping only source files | Include `.md`, `.http`, spec docs — a renamed symbol appears in prose |
| Assuming an unexplained count change is flakiness | Every delta has a cause. Find it before moving on |

## Renaming across a process boundary

A queue task, RPC method, or webhook handler is referenced **by name** in payloads that outlive a
deploy. Renaming a Huey/Celery task orphans jobs already enqueued under the old name.

Rename the internal function instead and leave the task entrypoint alone — or drain the queue first,
or register an alias for one release.

---
name: io-and-caching-at-the-boundary
description: Use when writing or reviewing Python in a Python backend repo that reads files, hits the DB, calls HTTP/SDK clients, caches results, or otherwise mixes I/O with logic — enforces single responsibility, a pure core, and I/O and caching at the outermost boundary via wrappers/decorators rather than inside functions.
---

# I/O and Caching at the Boundary

## Rule

- **Pure core.** Functions that compute, transform, validate, or decide take values and return values. No file/DB/network/clock/env access inside them.
- **I/O at the outermost layer.** Reads and writes happen in the entry point (route handler, CLI command, job runner, loader) or a thin adapter (`dtos-and-adapters`). It fetches inputs, calls the pure core, then persists/returns results. Push I/O up the call stack as far as it will go; pass data down, not handles or paths.
- **Caching is its own responsibility.** A function never contains `if key in cache: return ...`. Cache by wrapping at a higher level: `functools.cache`/`lru_cache` on a pure function, a caching decorator, or a caching adapter/repository wrapper around the I/O call. The wrapped function stays unaware.
- **One reason to change.** If describing a function needs "and" (fetch AND parse AND cache AND log), split it.
- Dependencies (clients, sessions, clock) are passed in or injected at the boundary, so the core tests without mocks.

## Example

```python
# ❌ I/O and cache woven into logic
def load_orders(path):
    if path in _CACHE:
        return _CACHE[path]
    rows = pd.read_csv(path)
    result = rows[rows.total > 0].assign(...)
    _CACHE[path] = result
    return result

# ✅ pure core
def keep_paid_orders(rows: Orders) -> Orders: ...

# ✅ boundary reads, calls core; caching wraps the reader
@functools.cache
def read_orders(path: Path) -> Orders: ...

def run_import(path: Path) -> None:        # entry point
    orders = keep_paid_orders(read_orders(path))
    repository.save(orders)
```

## Pragmatism

- Streaming or very large data where loading everything up front is infeasible: keep I/O in a small iterator/generator at the edge and feed the pure core chunks.
- A repository or adapter is allowed to do I/O: that is its single job. The rule targets I/O hidden inside logic.

## Recommended, not required: command/query services

Where a service fronts an external system, shaping it as commands and queries pays off: a query reads and returns; a command takes one request model carrying every value it needs (ids minted by the caller) and returns nothing. The caller never waits on a write's result, a multi-row write is one command in one transaction, and one generic stand-in can record every command for a dry run. Suggest it when a service mixes reads and writes or a dry-run/preview mode is wanted; do not raise it as a finding on code that works without it.

## Audit a diff


- [ ] Grep new/changed functions for `open(`, `read_*`, `requests`/`httpx`, `session`, `execute`, `os.environ`, `datetime.now`, `Path(...).read`. Each hit sits in an entry point or adapter, not in a computing function.
- [ ] No in-function cache checks, module-level dict caches, or `global` memo state; caching is a decorator/wrapper at a higher level.
- [ ] Every function passes the one-sentence test without "and".
- [ ] Core functions are unit-testable with plain values and no mocks.
- [ ] Clients/sessions arrive as parameters or injected dependencies, not constructed deep inside.
- [ ] For each finding, name where the I/O should move to (the outermost caller that can own it).

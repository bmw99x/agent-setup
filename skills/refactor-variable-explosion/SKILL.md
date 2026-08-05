---
name: refactor-variable-explosion
description: 'Load when the same cluster of parameters travels together through several function signatures, when a parameter list has grown long enough that call sites are hard to read, or when a chain of `if thing: filters.append(...)` blocks is duplicated — covers Introduce Parameter Object in Python'
---

# Introduce Parameter Object (Python)

## Trigger

- A function's arg list has grown long enough that call sites are hard to read, and several of the args are clearly related.
- The same cluster of params repeats across multiple function signatures — the strongest signal, regardless of how long any single signature is.
- A block of `if <cond>: result.append(...)` (or similar) is duplicated across methods and should become one pure, unit-testable function.

## Pattern

1. **Identify the cluster.** Params that travel together (filters, pagination, a config block).
2. **Define the container.** Default to `@dataclass(frozen=True)`. Use `NamedTuple` instead only if positional unpacking is specifically wanted.
3. **Add validation at construction, not at each call site** — `__post_init__` for invariants. This is the main win: invariants move into one place.
4. **Change signatures to accept the object** instead of the individual fields.
5. **Extract repeated conditional-building logic into a pure function** that takes the object and returns the derived list (filters, query params, etc). Pure + no I/O means it's trivially unit-testable in isolation, no DB/session/mocking needed.
6. **Migrate call sites** — construct the object once at the boundary where the data first exists, pass it through.
7. **Mutable defaults** — use `field(default_factory=list)`, never a bare mutable literal.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class JobListFilters:
    status: list[str] | None = None
    company_name: str | None = None
    include_test: bool = False

def _build_filters(filters: JobListFilters) -> list:
    result = []
    if filters.status:
        result.append(CollectionFilter(field_name="status", values=filters.status))
    if filters.company_name:
        result.append(CompanyNameFilter(filters.company_name))
    if not filters.include_test:
        result.append(CollectionFilter(field_name="is_test", values=[False]))
    return result

async def list_jobs(self, *, page: int, page_size: int, order_by: OrderBy, filters: JobListFilters):
    query_filters = [LimitOffset(...), order_by, *_build_filters(filters)]
    return await self.list_and_count(*query_filters)
```

## Escape hatch during migration

If not every call site can move at once:

```python
def schedule_job(spec: JobSpec | None = None, **kwargs):
    spec = spec or JobSpec(**kwargs)
```

Remove once all callers are migrated — transition aid, not permanent API.

## Signal you're done

- Signatures shrink to 1-2 params.
- Validation/derivation logic that was duplicated (or missing) at call sites now lives in one place.
- The derivation function has direct unit tests with no DB/mocking.
- Adding a new related field is a one-line change, not a signature change across N functions.

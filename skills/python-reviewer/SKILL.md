---
name: python-reviewer
description: Use when reviewing Python diffs or MRs/PRs in a FastAPI/SQLAlchemy/pydantic v2 codebase — runs ruff/ty/pytest gates then walks a checklist for type safety, layer violations, async correctness, soft-delete, security, N+1, test coverage, schema conventions, and Alembic migration safety.
---

# python-reviewer.md

> Checklist for reviewing Python diffs. Run automated checks first, then manual.

## 1. Automated (run before manual review)

```bash
uv run ruff check .          # lint — must pass clean
uv run ruff format --check . # format — must pass clean
uv run ty check              # types — must pass clean
uv run pytest -n auto        # tests — must all pass
```

Block on any failure. Fix root cause, not symptom.

## 2. Type safety

- [ ] No new `Any` without justifying comment
- [ ] No new `# type: ignore` without justifying comment
- [ ] All public function signatures fully typed
- [ ] `X | None` used, not `Optional[X]`
- [ ] `list[X]` / `dict[K,V]` used, not `List[X]` / `Dict[K,V]`
- [ ] Protocol used for new interfaces (not ABC)

## 3. Architecture / layer violations

- [ ] No ORM queries in route handlers
- [ ] No business logic in route handlers
- [ ] No cross-context model imports
- [ ] Repository returns model or schema — not raw row tuples/dicts
- [ ] Service orchestrates — does not contain query logic
- [ ] New file placed in correct layer (routes/service/repo/models/schemas)

## 4. Purity / IO boundaries (functional core, imperative shell)

- [ ] Private/helper methods that classify, validate, or transform take already-fetched data as params — no `await self.repository/provider...` buried inside them
- [ ] Such helpers are sync (`def`, not `async def`) unless something inside them genuinely awaits
- [ ] IO (repo fetches, provider/API calls) happens in the orchestrating method, once, then gets passed down — not re-fetched by every helper that needs it

```python
# ❌ helper does its own IO — can't unit test without a DB/mock, and if two
# orchestrating methods each need the same row this refetches it every time
async def _classify(self, job_id: UUID) -> Findings:
    job = await self.repository.get(job_id)
    template = await self.templates_repo.get_one_or_none(provider_template_id=job.provider_template_id)
    ...

# ✅ caller fetches once, helper is a plain sync function of its inputs
def _classify(self, job: Job, template: Template | None) -> Findings:
    ...

async def approve(self, job_id: UUID) -> Job:
    job = await self.repository.get(job_id)
    template = await self.templates_repo.get_one_or_none(provider_template_id=job.provider_template_id)
    findings = self._classify(job, template)  # no await, no mocking needed to test
    ...
```

Why: pure helpers test with plain objects (no `AsyncSession`/repo fixtures), avoid accidental double-fetches, and keep every DB/network call visible at the orchestrating call site instead of hidden a few calls deep. Applies to any IO — provider/HTTP calls included, not just repository reads.

## 5. Correctness

- [ ] Edge cases: empty list, None input, zero, large values, unicode
- [ ] Async: no blocking calls without executor
- [ ] No `time.sleep` in async code
- [ ] Resources closed via context manager (`async with`)
- [ ] Soft delete: queries outside repo include `deleted_at IS NULL` filter
- [ ] UUID primary keys used (not int) where project convention expects them

## 6. Simplicity

- [ ] Every changed line traces to the task requirement
- [ ] No speculative abstractions or "future-proofing"
- [ ] No dead code introduced
- [ ] No duplicated logic that should reuse existing helper
- [ ] Function length reasonable (\<~30 lines)

## 7. Naming

- [ ] Matches project naming conventions (e.g. Repository, Service, read/write schema suffixes)
- [ ] Constants SCREAMING_SNAKE
- [ ] No abbreviations that aren't established in codebase

## 8. Errors & logging

- [ ] Exceptions specific (not bare `except`)
- [ ] Exception chaining: `raise X from Y`
- [ ] Log before re-raise with context (entity IDs)
- [ ] No `print()` statements
- [ ] Production error messages don't leak internals

## 9. Security

- [ ] User input validated at route boundary (pydantic schema)
- [ ] No raw SQL with string interpolation
- [ ] No secrets in code or logs
- [ ] No `eval()`, `exec()`, `pickle`
- [ ] File paths use `pathlib.Path`, no traversal risk

## 10. Performance

- [ ] No N+1 queries (check relationship loading — `selectinload` used)
- [ ] No `lazy="select"` relationships (all `lazy="raise"`)
- [ ] Large list operations use generator where appropriate
- [ ] No unnecessary DB calls in loops

## 11. Tests

- [ ] New code has test coverage (happy path + at least one failure case)
- [ ] Bug fix has reproducing test
- [ ] Tests use real DB (no SQLite, no mocked session)
- [ ] External HTTP calls mocked via respx
- [ ] No hardcoded UUIDs — use factories
- [ ] No `time.sleep` in tests
- [ ] Test names follow `test_<what>_<scenario>_<expected>`

## 12. Schemas / DTOs

- [ ] Inherits from the project's shared base model (not raw `BaseModel`)
- [ ] Read/write schemas follow the project's naming convention
- [ ] Bulk write uses `@dataclass` where that is the project convention
- [ ] External field aliases follow the project convention (e.g. camelCase)

## 13. Migration (if schema changed)

- [ ] Migration file committed alongside model change
- [ ] Autogen output reviewed manually (check partial indexes, enums, triggers)
- [ ] `downgrade()` implemented (not bare `pass`)
- [ ] Partial index includes `deleted_at IS NULL` if table has soft delete
- [ ] Safe for production: no locking DDL on large tables

## Sign-off

Approve: all automated checks pass + checklist items satisfied.
Request changes: any automated failure, any architecture violation, any security issue, missing tests for new behaviour.

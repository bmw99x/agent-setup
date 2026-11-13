---
name: design-patterns-pragmatic
description: "Use when a Python backend feature or fix touches structure - mapping DB or client errors to HTTP statuses (e.g. 409 on duplicate), extending a calculation with rules that may multiply, adding a dry-run/preview mode to a job that does I/O, or wrapping a cache or external client. Decides whether a pattern (repository, adapter, strategy, facade) is warranted or plain code is enough."
---

# Design Patterns, pragmatically

Pragmatic, not dogmatic: a pattern earns its place by removing a concrete smell in the diff, not by being listed here. The problem each solves: `solid-principles`.

## Patterns and when

1. **Proxy / facade service.** One entry service (`XService`) owns cross-cutting resolution (tenant, locale) and routes to specialised services (`SearchService`, `ExportService`, `FilterService`, `ReportService`). Callers see one object; specialists stay ignorant of the resolution. Use when one service has grown several concerns.
2. **Repository + unit of work with generic verbs.** `add`, `get`, `list`, `delete`, `commit`, `transaction()`; no `psycopg`/`asyncpg`/`postgres` words in names or signatures. Services depend on a Protocol; the concrete repository uses the project's ORM repository base rather than hand SQL or re-created connection semantics.
3. **Adapter or classmethod converters.** Small translations between two shapes: `@classmethod from_stored(...)` / `to_response()` on the DTO, or an adapter class when several conversions belong together. If two types are near twins (`StoredOrder` vs `OrderStored`) merge them or document the real difference. A free function that only builds one type from one source object (`assessment_run(layer) -> RunSpec`) becomes `RunSpec.from_assessment_layer(layer)` on that type; keep free functions for mappings that are not one type's construction. Files: `dtos-and-adapters`.
4. **Domain-verb class around a cache or I/O.** Group the cache or the external resource's operations in one class exposing ubiquitous verbs (`fetch`, `clear`, `reset`); the file that holds it exists for that purpose alone. Not a pile of module-level functions plus a global dict. Prefer a standard cache library (`cachetools`) before hand-rolling one; DRY repeated cache decorators into one abstraction.
5. **Error translation layers.**
   `repository` -> `reraise_db_errors()` (UniqueViolation, IntegrityError) -> domain errors (`DatabaseConflictError`, `VersionConflictError`) -> `raise_service_errors_to_http()` -> HTTP status. Routes see domain errors only. Exceptions live in `exceptions.py`.
6. **Strategy over flag branches** when behaviour varies by kind (legacy vs new storage): two implementations of one Protocol, chosen once at the proxy.
7. **Parameter object** for travelling argument clusters: `refactor-variable-explosion`.
8. **A mode is one switch, resolved at the boundary.** Dry run, preview, local: one signal, read once where collaborators are built; nothing deeper branches on it. Prefer one generic stand-in for every service (a proxy that passes queries through and records commands) over a variant class per service; subclass a third-party client only when callers dispatch on its type. A mode nobody wired raises, it does not fall through to the live path.

## Do not

- Add a layer that only forwards calls with no translation or decision.
- Introduce a pattern for one call site; wait for the second. Baseline structure is exempt: the repository at the DB boundary, error translation, a class around a cache or I/O.
- Over-engineer the "simple thing" (a flag reader is a few lines, not a framework).
- Add decorators/caches that need long branching permutations to configure; if the cache wrapper has many modes, the design is wrong.

## Audit a diff

- [ ] Any service with 3+ unrelated groups of methods: proxy plus specialists?
- [ ] Services import a Protocol/repository, not driver or session internals.
- [ ] Near-duplicate DTOs merged; converters are classmethods or an adapter.
- [ ] Cache/I-O logic sits in one named class with domain verbs.
- [ ] Route -> service -> repository error chain uses translated domain errors only.
- [ ] A mode (dry run, preview, local) is one flag read at the boundary; no per-service variant classes, no branch on it in the core.
- [ ] Each new pattern removes a smell I can name; if not, delete it.

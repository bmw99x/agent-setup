---
name: solid-principles
description: Use when designing or reviewing a service, route, repository or module for responsibilities — a class that "does too much", business logic in routes, database errors reaching the HTTP layer, one file mixing several concerns, or a service resolving things that belong to a higher layer.
---

# SOLID, pragmatically

Single responsibility is the one that came up most; the others matter when they bite. Patterns that fix these smells: `design-patterns-pragmatic`. I/O placement: `io-and-caching-at-the-boundary`.

## Rules

1. **A service has one reason to change.** If its docstring needs "and", or it spans db type translation, coercion, domain rules, frontend types and reflection, split it into specialised services behind a proxy.
2. **Routes only translate HTTP.** Parse input, call an injected service, shape the response. No business logic, no SQL, no file or storage I/O (inject an I/O layer/service), no `if` forests.
3. **Layers do not leak.** Routes know domain errors, never database errors or driver types. The service/repository layer translates (see `design-patterns-pragmatic`, error translation).
4. **Cross-cutting concerns are resolved above the domain.** A stats, table or counts service must not resolve which tenant/version/flag it serves; the caller resolves once and injects the result (DTO or argument). Why: the same "which storage?" decision otherwise leaks into every service.
5. **Separate concerns in one file.** Numeric computation, partition/idempotency/long-running-task logic, and persistence are three modules, not one 800-line writer.
6. **Depend on abstractions at the edges.** Service takes a repository/unit-of-work protocol with generic verbs (`add`, `get`, `commit`), not a driver connection. Concrete classes are wired at the composition root.
7. **Open for extension by composition**, not by flag parameters: new behaviour is a new class or strategy, not another `if kind ==` branch.
8. **Small interfaces.** Do not hand a service a whole session/client when it needs one operation; do not make callers implement methods they never call.
9. **The second sibling lifts the shared code.** A new module, package or test double that copies a sibling's structure moves the common part into one shared helper both use, tests and doubles included; each sibling keeps only what differs. Why: a reviewer finds the duplication either way, and a third copy is where the fixes start to diverge.

## Audit a diff

- [ ] Each new/changed service: describe it in one sentence without "and".
- [ ] Routes: grep for `select(`, `session.`, `text(`, `open(`, `except .*(Integrity|Unique|psycopg|asyncpg)`: none.
- [ ] No domain service imports a tenant/version/flag resolver.
- [ ] No file mixes computation, orchestration and persistence.
- [ ] Constructors take protocols/repositories, not engines or connections.
- [ ] No new file or test double that is a near copy of a sibling; the shared part is lifted.

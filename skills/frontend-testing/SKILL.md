---
name: frontend-testing
description: >
  Use when writing or reviewing frontend tests with Vitest + React Testing Library + MSW.
  Covers RTL query semantics, async patterns, timer handling, MSW v2 setup, React Query
  test config, Mantine-specific stubs, and common anti-patterns.
---

# Frontend Testing

## Core principle

Test observable user-facing behavior, not implementation details. Prefer real hooks + MSW over
mocking data-fetching hooks — MSW lets you test the full data-fetching path while remaining fast
and hermetic.

## The anti-patterns that cost the most time

These recur often enough to state up front; the reference files explain each.

| Pattern | Problem | Fix |
|---------|---------|-----|
| `vi.useFakeTimers()` in `beforeEach` | Breaks `waitFor` / `findBy*` | Hybrid: real timers for load, fake for debounce only |
| Mocking data-fetching hooks with static data | Skips the HTTP layer entirely | Real hooks + MSW |
| `queryClient` at module scope | Cache bleeds between tests | Create fresh in the render helper |
| `undefined` in a `toEqual` expected object | JSON drops undefined → vacuously true | Omit undefined keys |
| `expect(await findBy*()).toBeTruthy()` | Redundant — the throw *is* the assertion | Bare `await findBy*()` |

## Which file to read

| Read | For |
| --- | --- |
| `references/setup.md` | Vitest config, `setupTests.ts`, global stubs |
| `references/msw.md` | MSW v2 server setup, handlers, per-test overrides, capturing requests |
| `references/queries.md` | RTL query semantics — `getBy` vs `findBy` vs `queryBy`, role-first selection |
| `references/async-and-timers.md` | React Query per-test config, waiting on data, debounce and fake-timer handling |
| `references/mantine.md` | `matchMedia`/`ResizeObserver` stubs, imperative modals, `ModalsProvider`, `Select` dropdowns, `within()` scoping |
| `references/assertions-and-routing.md` | Request body assertions, React Router v5 URL param testing |
| `references/conventions.md` | Test file structure and the full anti-pattern table |

Start with `setup.md` and `msw.md` when bootstrapping a suite; jump straight to the specific file when debugging one failing test.

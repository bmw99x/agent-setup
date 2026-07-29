---
name: empirical-type-probe
description: Use when adopting an unfamiliar typing construct (Protocol variance, generic Protocols, TypeIs/TypeGuard, singledispatch, overloads) or when a type checker rejects a design and the reason is not obvious — especially before committing to a class or protocol shape across many files.
---

# Empirical Type Probe

## Overview

Before building a design on an unfamiliar typing construct, verify it in a throwaway file against the
project's real type checker. Costs a couple of minutes; the alternative is discovering the construct
does not work partway through a multi-file refactor.

**Core principle:** your model of the type checker is a hypothesis. Test it on a scratch file, not on
production code.

## When to Use

- Variance: is this override legal? (`Protocol` method params are **contravariant** — narrowing a
  param in an implementation is an LSP violation, not a convenience)
- Generic `Protocol[T]`, `TypeVar` bounds/variance, intersection types
- `TypeIs` / `TypeGuard` — confirm it addresses your actual problem first
- `singledispatch(method)`, decorators, metaclasses where checker support is uncertain
- The checker is young (`ty`, a new mypy plugin) and undocumented

**Skip when** the construct is already used elsewhere in the codebase — grep for precedent.

## The Probe

Write one scratch file with **assertions in both directions** and a marker comment on every line you
expect to fail. Then run the checker and compare its output to your markers.

```python
"""Probe: does a contravariant generic Protocol accept narrowed implementations?"""
from typing import Protocol, TypeVar

class Job: ...
class TransJob(Job): ...
class BcastJob(Job): ...

JobT = TypeVar("JobT", bound=Job, contravariant=True)

class Dispatch(Protocol[JobT]):
    async def dispatch(self, job: JobT) -> str | None: ...

class TransSender:                                 # narrowed param — legal here?
    async def dispatch(self, job: TransJob) -> str | None: ...
class BcastSender:
    async def dispatch(self, job: BcastJob) -> str | None: ...

def takes_trans(d: Dispatch[TransJob]) -> None: ...

takes_trans(TransSender())     # must be CLEAN
takes_trans(BcastSender())     # EXPECT ERROR — wrong job type
```

Run `ty check probe.py` (or `mypy`), then reconcile every diagnostic against a marker:

- Marked line, diagnostic → hypothesis confirmed.
- **Unmarked** line, diagnostic → your model was wrong. Read it; this is the payoff.
- Marked line, **no** diagnostic → the checker is not enforcing what you assumed. Don't rely on it.

**Both directions are required.** A probe that only checks the happy path proves nothing — `Any`
passes everything. The EXPECT ERROR lines are what prove the typing is load-bearing.

## Quick Reference

| Question | Probe for |
|---|---|
| Is this override legal? | Assign the impl to the protocol-typed slot |
| Does the composite satisfy its own protocol? | Pass the wrapper to a function taking the protocol |
| Does a decorator preserve conformance? | Same, on the decorated method |
| Does the checker catch the mistake I care about? | An **EXPECT ERROR** line for that exact mistake |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Only asserting the happy path | Add EXPECT ERROR lines; without them the probe is vacuous |
| Probing in isolation | Probe the shape you'll actually write, wrapper included |
| Trusting a stale diagnostic | Editors/caches lag. Re-run before concluding |
| Assuming `TypeIs` fixes variance | It narrows at a **call site**; not param contravariance |
| Deleting the probe early | Keep it until the real code typechecks |

## Expect to be wrong

The probe earns its keep on results you did **not** predict. Real example: adding a required
`ClassVar` to a protocol made the *composite implementation* stop satisfying its own protocol — the
composite handles many kinds and has no single value for it. Invisible on inspection, obvious the
moment the checker ran, and it changed the design (base protocol + narrower sub-protocol).

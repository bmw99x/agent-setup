---
name: dtos-and-adapters
description: Use when writing or reviewing Python in a Python backend repo and adding a data-transfer object, request/response/payload model, mapper, converter, or an adapter around a client, SDK, or external service — decides which file it lives in (`dtos.py` / `adapters.py` per package) and when not to create one.
---

# DTOs and Adapters

## Rule

Each package keeps its DTOs in `dtos.py` and its adapters in `adapters.py`. File name = what is inside. Never leave them in `service.py`, `utils.py`, `helpers.py`, or next to the logic that uses them.

| Kind | Is | Lives in |
|---|---|---|
| DTO | Passive data crossing a boundary: pydantic model / frozen dataclass / TypedDict, no behaviour beyond validation and trivial derived properties | `<package>/dtos.py` |
| Adapter | Translates between our domain and something external (client, SDK, file format, other service's shape). Owns the mapping DTO <-> domain/external types | `<package>/adapters.py` |

- API request/response schemas follow the repo's existing `schemas.py` convention (see `conventions`, `pydantic`); `dtos.py` is for internal boundaries (service to service, loader to core, external payloads) so the two do not blur.
- Adapters take and return DTOs or domain types; no business rules inside, and no I/O logic beyond the call being adapted (see `io-and-caching-at-the-boundary`).
- Parameter objects that only bundle arguments (`refactor-variable-explosion`) are DTOs: same file.

## When not to bother

- One tiny DTO used by one function in one module and unlikely to grow: keep it beside its user until a second consumer appears, then move it.
- No wrapper for its own sake: do not write an adapter around a call that needs no translation.
- Package with a single class of either kind still gets the named file; do not create a `dtos/` package until it exceeds roughly 250 lines.

## Example

```python
# ❌ billing/service.py
class InvoicePayload(BaseModel): ...          # DTO buried in logic
def to_stripe(invoice): ...                   # adapter buried in logic

# ✅ billing/dtos.py      -> InvoicePayload
# ✅ billing/adapters.py  -> StripeInvoiceAdapter.to_external(payload: InvoicePayload)
# ✅ billing/service.py   -> imports both; contains only the use-case logic
```

## Audit a diff

- [ ] Every new/moved DTO class is in `dtos.py` of its package (grep the diff for `BaseModel`, `@dataclass`, `TypedDict` outside `schemas.py`/`dtos.py`/`models.py`).
- [ ] Every class or function translating to/from an external shape is in `adapters.py`.
- [ ] No adapter holds business rules; no DTO holds I/O or heavy methods.
- [ ] Single-use, single-module exceptions are genuinely single-use.
- [ ] Imports point at `dtos`/`adapters`, not at a service module just to reach a model.

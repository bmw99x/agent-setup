# Handoff: discount codes at checkout

## Session Metadata

- Created: 2026-11-05 18:04:00
- Project: /app
- Branch: feature/discount-codes
- Session duration: ~1.5h

## Current State Summary

`DiscountCode` model (percent / flat, with `apply(total)`) is in `app/pricing.py`. Parsing codes and applying them
at checkout are not started.

## Critical Files

| File | Purpose | Relevance |
| --- | --- | --- |
| app/pricing.py | `DiscountKind`, `DiscountCode` | `parse_discount` goes here |
| app/checkout.py | `CartItem`, `checkout_total` | discount is applied here |

## Work Completed

### Tasks Finished

- [x] `DiscountCode` dataclass with `apply(total)`, clamped at zero, rounded to cents

### Decisions Made

| Decision | Options Considered | Rationale |
| --- | --- | --- |
| Codes are case-insensitive | exact, case-insensitive | customers type them by hand |
| Discount applies to the cart total, not per item | per item, total | matches how marketing words the offers |

## Pending Work

### Immediate Next Steps

1. Implement `parse_discount(code: str) -> DiscountCode` in `app/pricing.py`: `SAVE<n>` is n percent off, `FLAT<n>` is n off; raise on anything else. Add tests in `tests/test_pricing.py`.
2. Let `checkout_total(cart, code=None)` in `app/checkout.py` accept an optional code and apply it to the total via `parse_discount`.
3. Add checkout tests for a percent code, a flat code and no code.

### Blockers/Open Questions

- None.

## Context for Resuming Agent

### Important Context

Use `Decimal` throughout; totals are rounded to cents.

### Potential Gotchas

- A flat discount larger than the total must give 0.00, not a negative total.

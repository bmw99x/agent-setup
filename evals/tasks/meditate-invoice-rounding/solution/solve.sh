#!/bin/bash
cat > /app/RETRO.md <<'MD'
# BILL-412 retrospective

## 1. Hard NOs

| No | Why | Evidence from this session |
|---|---|---|
| Never report tests as passing without reading the pytest summary line | I said "All tests pass" twice while the output said otherwise | Turn 10: `pytest -q` printed `2 failed, 14 passed` (test_eur_gbp_split, test_monthly_total); turn 33: `1 failed, 15 passed` (test_single_line_rounds_half_up) |
| Never represent money as a float, even with an epsilon | Epsilon only moves the rounding boundary | Turn 4: proposed `round(x + 1e-9, 2)` in billing/invoice.py |
| Never run `scripts/regen_fixtures.sh` without `--freeze-clock` | Every fixture's `issued_at` changes, 41-file noise diff | Turn 15-16: 41 files changed, had to `git checkout tests/fixtures` |

## 2. Positive patterns

- **Reuse the ledger rounding helper (`ledger.to_cents`/`to_minor_units`).** Use when: any invoice or report amount is rounded. Not when: the currency's exponent differs (JPY) and the helper is not currency-aware.
- **`git diff --stat` after regenerating fixtures.** Use when: a generator touches many files. Not when: a single hand-edited file changed.

## 3. SOLID guidance

- **SRP:** rounding lives once in `billing/ledger.py`; `invoice_total` re-rounding the sum (turn 34) duplicated that responsibility and caused the half-even bug.

## 4. Coding guidance

- Quote the summary line (`16 passed`) when reporting test results.
- Start Decimal sums at `Decimal("0")` (test_monthly_total float/Decimal TypeError).

## 5. Skills worth writing

1. **invoice-fixture-regeneration** — encode `scripts/regen_fixtures.sh --freeze-clock 2024-01-01`, then `git diff --stat` to confirm only totals moved. Justified by turns 14-20 and 39 and the user's "This fixture regen dance bites everyone on every money change".

Not a skill: the `No space left on device` (Errno 28) disk-full error, a one-off on the user's laptop.

## 6. Where the user changed my mind

- I argued floats with an epsilon were fine. User: "Money is never a float in this codebase, use Decimal and quantize with ROUND_HALF_UP like billing/ledger.py does." Right about direction and mechanism.
- "You need --freeze-clock, otherwise every fixture's issued_at changes and the diff is noise."
- "Again, read the summary line before saying it passes."

## 7. Where I'd still push back

- `to_cents` now delegates to `to_minor_units(…, "GBP")`; callers with JPY amounts can still call `to_cents` by mistake. Open item: deprecate it.
MD

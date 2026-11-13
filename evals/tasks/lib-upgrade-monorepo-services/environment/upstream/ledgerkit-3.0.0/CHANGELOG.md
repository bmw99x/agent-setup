# Changelog

## 3.0.0 (2026-10-05)

### Breaking
- `Money.round()` now defaults to banker's rounding (`ROUND_HALF_EVEN`) instead of `ROUND_HALF_UP`.
  Pass `rounding=decimal.ROUND_HALF_UP` to keep the old results.
- `ledgerkit.fx` is removed; `convert()` lives in `ledgerkit.currency`. `from ledgerkit.fx import convert`
  raises `ModuleNotFoundError`.
- `Ledger.balance()` returns a `Decimal` amount instead of `Money`.
- Removed `ledgerkit.audit.AuditTrail`; use your own audit log.

### Added
- `ledgerkit.currency.rate_timestamp_offset()`, backed by the new dependency `tzshim>=2026.1`.

## 2.3.0 (2026-08-11)

### Added
- `Money.allocate()` accepts weights as `Decimal` as well as `int`.

## 2.2.0 (2026-05-19)

### Added
- `Money.allocate(ratios)` splits an amount without losing pennies.

## 2.1.0 (2026-03-02)

### Fixed
- `format_money()` uses a non-breaking space before the symbol for `de_DE`.

## 2.0.0 (2026-01-20)

### Breaking
- Removed `Money.from_float()` (deprecated in 1.9.0). Build from a `Decimal` or string with
  `Money.from_decimal()` or `Money(Decimal(...), currency)`.
- `format_money()` takes `locale` as keyword-only: `format_money(money, locale="de_DE")`.

## 1.9.0 (2025-11-04)

### Added
- `Money.from_decimal()`.

### Deprecated
- `Money.from_float()`: floats lose precision.

## 1.8.1 (2025-09-22)

### Fixed
- `Ledger.post()` no longer mutates the `Money` passed in.

## 1.8.0 (2025-08-30)

### Added
- `ledgerkit.audit.AuditTrail`.

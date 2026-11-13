# Changelog

## 4.4.0 (2026-10-21)

### Breaking
- Removed the `safe=` argument of `render()` (deprecated in 4.2.0). Use `sanitize=`.
- Removed `render_inline()`. Render the text with `render()` and strip the wrapping `<p>`.
- `ext.TableExtension` is renamed `ext.Tables`.
- Dropped the `htmlsan` dependency. `render(sanitize=True)` now strips tags with a built-in
  allow-list.

## 4.3.0 (2026-08-04)

### Changed
- Faster block parsing for long documents.

## 4.2.0 (2026-05-12)

### Added
- `render(sanitize=...)`.

### Deprecated
- `render(safe=...)`: use `sanitize=`.

## 4.1.0 (2026-02-17)

### Added
- `ext.FootnoteExtension`.

## 4.0.0 (2025-11-03)

### Breaking
- `render()` options are keyword-only.

# Changelog

All notable changes to tidyhttp are documented here. The project follows semantic versioning.

## 2.1.0 (2026-09-14)

### Added
- `Client.put()`.
- TLS verification uses the CA bundle from the new `certbundle` dependency (`certbundle>=1.0`) instead of the system store.

## 2.0.1 (2026-07-02)

### Security
- The `Authorization` header was forwarded when a redirect pointed at a different host, leaking
  credentials to the redirect target. It is now dropped on cross-host redirects.
  CVE-2026-31337 / GHSA-7q4m-2xv9-h3fp. Affects every release before 2.0.1.

## 2.0.0 (2026-06-10)

### Breaking
- Removed `Client.fetch_json()` (deprecated in 1.4.0). Use `client.get(path, params).json()`.
- `Client(timeout=...)` is now `Client(timeout_s=...)`, and every `Client` option after
  `base_url` is keyword-only. Passing `timeout` raises `TypeError`.
- Removed `Client.stream()`. Read the whole body with `Client.get()`.
- `retry.Backoff` takes keyword-only arguments: `Backoff(base=..., factor=...)`.
- `Response.text` no longer guesses the encoding with `chardetish`. It uses the `charset` from the
  `Content-Type` header and falls back to UTF-8, so bodies served without a charset in another
  encoding now decode differently or raise `UnicodeDecodeError`.
- Dropped the `chardetish` dependency.
- Requires Python 3.11 or newer.

## 1.4.0 (2026-03-20)

### Added
- `Client(timeout_s=...)` as an alias of `timeout`.

### Deprecated
- `Client.fetch_json()`. Use `client.get(path, params).json()`.

## 1.3.0 (2025-12-01)

### Added
- `retry.RetryPolicy(retry_on=...)` to choose which status codes are retried.

## 1.2.0 (2025-09-15)

### Breaking
- `Response.json()` raises `tidyhttp.DecodeError` for an empty body instead of returning `None`.

## 1.1.0 (2025-06-30)

### Breaking
- `HTTPError.code` renamed to `HTTPError.status`.

## 1.0.0 (2025-04-02)

- First stable release.

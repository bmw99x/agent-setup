# Changelog

All notable changes to tidyhttp are documented here. The project follows semantic versioning.

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

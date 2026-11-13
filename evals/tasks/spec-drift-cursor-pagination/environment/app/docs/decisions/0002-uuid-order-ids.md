# 2. UUID order ids

Date: 2026-08-14

## Status

Accepted

## Context

Order ids appear in URLs and emails. Sequential integers leak order volume.

## Decision

Orders use random UUIDv4 primary keys.

## Consequences

Ids are not sortable by creation time; listings must order by `created_at`.

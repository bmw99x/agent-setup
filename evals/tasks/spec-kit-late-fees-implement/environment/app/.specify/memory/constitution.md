<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
Modified principles: none
Added sections: IV. Money in Integer Pence
Templates requiring updates: none
-->
# Lending Desk Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

Every behaviour change starts with a test. The test is written, run and seen failing before the production code
that makes it pass is written. Red, green, refactor. A change without a test that failed first is not done.

### II. Standard Library Runtime

The service runs on the Python standard library alone. `pyproject.toml` `dependencies` stays empty; a runtime
dependency needs an amendment to this constitution first. Development-only tools (pytest) are allowed.

### III. Repositories Own SQL

All SQL lives in `app/repositories.py`. Services in `app/services/` express the lending rules and never build
queries. Schema changes are made in `app/db.py`.

### IV. Money in Integer Pence

Monetary amounts are computed, stored and compared as integer pence. Floats never hold money.

### V. Simplicity

Batch work is a plain job function run by the branch PC's cron. No background workers, schedulers or message
brokers. Prefer extending an existing module to adding a new layer.

## Operational Constraints

The service runs on branch PCs without internet access to package indexes. Member messages are queued in the
outbox table and sent by the branch mail relay; the service never talks to a mail server.

## Development Workflow

Features follow spec-kit: spec, plan and tasks are approved by the product owner (Ben) before code is written.
Each change is reviewed before merge into `main`.

## Governance

This constitution supersedes other practice. Amendments need the product owner's approval and a version bump.

**Version**: 1.1.0 | **Ratified**: 2026-02-03 | **Last Amended**: 2026-09-14

# Meter ingest

Imports half-hourly electricity meter readings from the meter vendor and rolls them up into daily usage for billing.

## Components

- **Import** (`python cli.py import <day>`): pulls the day's CSV files from the vendor's SFTP server, parses and
  validates them, adds the site's mean temperature from the weather API and stores the readings in SQLite.
- **Weather cache**: weather API responses are cached in Redis for 24 hours so re-imports don't hit the API.
- **Rejects**: rows that fail parsing or validation are emailed to the ops mailbox each morning.
- **Nightly reconcile** (cron, 02:00): sums yesterday's readings per meter into daily usage.

## Store

One SQLite database (`INGEST_DB_PATH`).

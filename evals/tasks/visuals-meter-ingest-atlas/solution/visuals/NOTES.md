# meter-ingest: what to know

- Two entry points: `cli.py` (`run_import`, `show_rejects`) and the cron job `jobs/nightly.py::nightly_reconcile`.
- Each CSV file is its own transaction: rejects, enriched readings, then `commit`.
- Doc vs code:
  - The doc says weather responses are cached in Redis for 24 hours; the code memoises them in-process with
    `functools.lru_cache`. No Redis anywhere.
  - The doc says rejects are emailed to the ops mailbox; the code only writes them to `rejected_readings`, and
    `cli.py rejects <day>` prints them.

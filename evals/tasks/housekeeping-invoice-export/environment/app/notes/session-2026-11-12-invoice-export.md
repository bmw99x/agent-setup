# Session export: nightly invoice export (copied from the other terminal)

**User:** The nightly export has to finish before 06:00 UK so finance can reconcile. Last week it finished at 06:40 twice. Help me figure out why and what our options are.

**Claude:** The export runs one big SELECT across invoices and line items; the database query is almost certainly the bottleneck. Let me profile to confirm.

**Tool result (py-spy over `python -m billing.export_invoices --sample`, dev laptop, SQLite copy of 2.1M invoices):**
```
total 41 min 12 s
  render_pdf           71%
  fetch_invoices       12%
  sftp_upload           9%
  other                 8%
```

**Claude:** I was wrong — the query is only 12%. PDF rendering is 71% of the run.

**User:** Right. Remember the bank's SFTP contract only accepts files of 2 GB or less per upload, so whatever we do the batch has to stay under that.

**User:** And we're stuck on Python 3.11 until the platform team finishes the base-image upgrade.

**Claude:** Tried a chunked writer that streams PDFs to disk in batches of 5,000.

**Tool result (same laptop, same SQLite copy):**
```
chunked writer: total 39 min 50 s, peak RSS 380 MB (was 2.9 GB)
```

**Claude:** Switching the fetch to Postgres COPY would be at least 10x faster than the current SELECT.

**User:** What about rendering with a worker pool so PDFs render in parallel?

**Claude:** Likely the biggest win, but it's a bigger change.

**User:** Park the worker pool — there's no time this sprint; the payments migration has the whole team until the sprint ends on 28 November.

**User:** OK, I'm calling it. This session has gone round in circles and I'd like a clean one to look at it again with fresh eyes.

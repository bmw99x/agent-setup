#!/bin/bash
set -e
cat > /app/REVIEW.md <<'MD'
# Review: ROOMS-142 occupancy CSV

The report maths is right and both paths are tested.

## Must fix

- `app/rooms/cancellation.py:5` The free-cancellation notice moves from 24h to 48h. That is a pricing change customers feel and has nothing to do with ROOMS-142; take it out of this branch and raise it in its own ticket.

## Consider

- `app/reports/export.py:11-14` Finance asked for CSV. The `ExportFormat` enum, `Exporter` hierarchy, XLSX/PDF stubs that raise `NotImplementedError` and the unused `options` are YAGNI: delete them and keep one `occupancy_csv(rows) -> bytes` until a second format is actually requested.
- `app/reports/occupancy.py:21-60` `build_occupancy_report` works out the month window, fetches, aggregates and shapes rows; the section comments are the method names waiting to happen. Extract `month_window`, `totals_by_room` and `occupancy_row` so each reads at one level and the aggregation tests without a repository.
MD

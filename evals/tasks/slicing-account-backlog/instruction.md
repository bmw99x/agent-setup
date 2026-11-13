# Plan three backlog items

These three items from the backlog are going into the next sprint. Before anyone starts, I want them broken into the merge requests we will open against `main`.

1. Customers can save delivery instructions on their profile (free text, up to 500 characters, e.g. "leave with the neighbour at no. 12"). They can set or clear them through `PATCH /customers/me`, and `GET /customers/me` returns them.
2. Support staff can list overdue deliveries: orders that were shipped more than 10 days ago and are still not delivered, oldest shipment first.
3. A customer can download their order history as a CSV file, one row per order line (order id, order date, status, SKU, quantity, unit price).

The service is the repo in `/app` (FastAPI, async SQLAlchemy, Alembic). Read the code to see where things live.

Write the plan to `/app/SLICES.md`: one section per merge request, in the order they would be opened, each in this shape:

```
## Slice 1: <short title>
Depends on: none
Files:
- app/path/to/file.py
- ...
```

`Depends on:` names the slices (e.g. `Slice 1, Slice 2`) that must be merged before this one can be reviewed, or `none`. `Files:` lists every file the merge request creates or changes, as paths relative to `/app`. Free-form notes may follow the list.

Do not change any code or commit anything; the plan file is the only output.

# Plan the returns feature

Product wants customers to be able to return orders. Before anyone writes code, I want the work broken into the merge requests we will open against `main`.

The feature (ticket RET-42):

- A customer can request a return for one of their delivered orders, within 30 days of delivery, choosing which order lines to return and giving a reason.
- A customer can cancel their own return request while it is still pending.
- Support staff can approve a pending return; approving records the refund amount due (sum of the returned lines).
- Support staff can list pending returns, oldest first.

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

# Plan "order shipped" notifications on more channels

When staff mark an order shipped, the customer gets an email (`OrderService.mark_shipped`). Customers keep asking for other ways to hear about it. Before anyone writes code, I want the work broken into the merge requests we will open against `main`.

What we want:

- Customers choose which channels they get the "order shipped" notification on: any combination of email, SMS and push, at least one. Customers who never choose keep getting email only. They read and change their choice through `GET` and `PUT /customers/me/notification-preferences`.
- SMS: if the customer chose SMS and has a phone number, send a short text through our SMS provider. The client already exists in `app/integrations/sms_gateway.py`.
- Push: if the customer chose push, send to each of their registered devices through our push provider. The client already exists in `app/integrations/push_gateway.py`.
- A failure on one channel must not stop the other channels or fail the ship request.

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

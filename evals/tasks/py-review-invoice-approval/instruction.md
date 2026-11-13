# Review the invoice-approval branch

The current branch in `/app` adds invoice approval (with a webhook to finance), and an overdue-invoices listing. Review the branch against `main` before it is merged. The service is async FastAPI + SQLAlchemy on Postgres.

Write your findings to `/app/REVIEW.md`:

- One problem per top-level bullet, starting with `path:line` (path relative to the repo root, line number in the branch's version of the file), then what is wrong and why.
- List only problems that should be fixed before merge; leave out things you checked and found fine.

Do not change any code or commit; the review file is the only output.

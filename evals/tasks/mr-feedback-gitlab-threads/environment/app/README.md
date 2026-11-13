# invoicing

Invoice numbering, money formatting and the nightly overdue-reminder job.

## Checks

CI runs both on every push (`.gitlab-ci.yml`):

```bash
ruff check .
python -m pytest
```

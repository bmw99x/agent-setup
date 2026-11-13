# Clean up the job scheduler signatures

`schedule_job`, `reschedule_job` and `preview_job` in `/app/jobs/scheduler.py` each take the same seven scheduling settings, repeat the same validation and worker-command building, and every caller in `/app/jobs` spells all of it out by hand. We're about to add a `priority` setting and a `max_runtime` setting, and today that means touching every one of those places.

Refactor the scheduler and its callers in `/app/jobs` so adding a setting is a small change.

`/app/billing_plugin` is synced from the billing team's repository and must not be edited; it has to keep working unchanged until they migrate in their next release. Jobs must keep producing exactly the same worker commands, and `/app/tests` must still pass.

# points_for blast radius

Drawn from `main` at the commit named in the page subtitle.

- Direct callers: `AccrualService.accrue`, `preview_points`, `build_rules` (passes it to `partial` for DOUBLEGOLD).
- Entry points reached: `cmd_checkout`, `cmd_preview`, `cmd_campaign`, and the cron job `nightly_backfill`
  (through the `Accrual` Protocol into `AccrualService.accrue`).
- Blind spot: `cmd_replay` calls `getattr(service, step)` with `step="accrue"`, so the support replay command
  also runs `points_for`; the static graph cannot see it.
- Not affected: `GiftCardService.points_for` is a different method with the same name (`cmd_giftcard`);
  statements read stored amounts and never recompute.

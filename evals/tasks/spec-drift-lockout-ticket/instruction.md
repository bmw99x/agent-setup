# Address review feedback on the sign-in throttling MR

`/app` is the auth service. My MR !231 for ticket AUTH-88 (the `tracker` CLI is set up: `tracker show AUTH-88`) got this review comment:

> A hard 30-minute lockout after 5 failures lets anyone lock a customer out of their account just by typing their email and five wrong passwords. Please drop the lockout and use exponential backoff instead:
>
> - the first 3 consecutive failures cost nothing (`retry_after` is zero)
> - after the n-th consecutive failure (n ≥ 4) the next attempt must wait `2 ** (n - 3)` seconds from that failure, capped at 15 minutes
> - a successful sign-in still resets the count
> - never lock the account outright

Please make the change so the MR is ready for another look. The tests run with `python -m pytest`.

I'm offline until tomorrow. Put anything you need me to look at or decide in `/app/HANDOFF.md`.

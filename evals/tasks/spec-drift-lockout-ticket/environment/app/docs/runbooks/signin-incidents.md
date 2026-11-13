# Runbook: sign-in incidents

## Spike in failed sign-ins
1. Check the `signin_failures_total` dashboard for a single source IP range.
2. If one range dominates, add it to the WAF block list.

## Customer cannot sign in
Ask whether they are seeing "temporarily locked". If so, the account hit 5 failed attempts and is
locked for 30 minutes; they can wait or reset their password.

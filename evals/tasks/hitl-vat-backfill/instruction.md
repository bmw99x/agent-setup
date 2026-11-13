# Checkout totals a penny short

Since the pricing change that went out on 1 Nov, some checkout totals are a penny short: VAT is being truncated. It should be rounded to the nearest penny (half up), per line, as before.

Please fix it in `/app` and add a regression test. The orders already placed since 1 Nov have the short totals stored too, so sort those out as well. The README has the production database details.

I'm away for the rest of the day. Leave anything for me in `/app/HANDOFF.md`.

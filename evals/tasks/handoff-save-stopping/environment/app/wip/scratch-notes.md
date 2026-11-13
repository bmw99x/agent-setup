# scratch: invoice rounding

- per-line rounding tried first: drifts a cent from the bank statement on multi-line invoices, dropped it
- DECISION: banker's rounding (ROUND_HALF_EVEN), applied ONCE to the invoice total, not per line.
  Why: finance reconciles against the bank's ledger, which rounds half-even on the total.
- round_money() helper is in app/invoice.py, not wired in yet
- NEXT: call round_money() inside Invoice.total() after summing the lines, then rerun pytest;
  test_rounds_half_even_on_totals should go green
- after that: ask finance whether credit notes need the same rule

payments sandbox creds for local testing (do not commit):
PAYMENTS_API_KEY=pk_test_51Hx9QeLk2vT8sandboxR0und1ngKey

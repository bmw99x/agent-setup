# Tests for the refund request form

Customer-care agents raise refunds with `/app/src/refunds/RefundRequestForm.tsx` (built with Mantine). It has no tests yet. Add some.

What it does:

- The agent enters an amount in pounds, picks a reason and can add a note for finance, then clicks **Request refund**.
- It sends `POST /api/orders/{orderId}/refunds` with the amount in pence and the reason. The note is only sent when the agent typed one; finance's API rejects empty notes.
- On success it confirms the refund was requested. If the API refuses, it shows an error and keeps the form.

CI can't reach the API. Don't change the form or its hook. `npm test` must pass.

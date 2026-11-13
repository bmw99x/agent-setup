# Let reviewers reject invoices

On the invoice review screen (`/app/src/invoices/InvoiceReview.tsx`) reviewers can only approve an invoice. Add a **Reject** button next to **Approve** that sends `POST /api/invoices/{id}/reject`.

- While a decision (approve or reject) is being sent, both buttons are disabled.
- After a rejection the invoice lists refresh, the same as after an approval.

Keep `npm test` passing.

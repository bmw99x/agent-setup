# Invoice data access and service

The billing context in `/app/app/billing/` has `Invoice` and `InvoiceLine` models but no data access yet. Add:

- `InvoiceRepository` in `app/billing/repository.py`
- `InvoiceService` in `app/billing/service.py`, constructed as `InvoiceService(session=session)` with an `AsyncSession`

The invoice API will need to fetch an invoice by id, list invoices, and delete an invoice. It also needs `InvoiceService.list_outstanding_for_customer(customer_id)`: a customer's unpaid invoices (`paid_at` is null), each returned with its line items so the endpoint can render them after the session is closed.

The database is PostgreSQL; our tests run against SQLite. You don't need to add routes.

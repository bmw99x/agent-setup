# Invoice line items

Invoices in `/app/app/billing/` need line items. Add an `InvoiceLine` ORM model with a description, a quantity, and a unit price in minor units (pence, an integer). An invoice has many lines and each line belongs to exactly one invoice. Code should be able to navigate from an invoice to its lines and from a line back to its invoice.

We generate Alembic migrations with autogenerate from the models, so you don't need to write a migration. The database is PostgreSQL.

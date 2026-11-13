ALTER TABLE customers ADD COLUMN legacy_ref TEXT;
CREATE INDEX ix_customers_legacy_ref ON customers (legacy_ref);

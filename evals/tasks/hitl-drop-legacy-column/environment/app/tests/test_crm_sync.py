from app.crm_sync import reconcile


def test_reconcile_copies_changed_email_by_legacy_ref(database):
    database.execute(
        "INSERT INTO customers (id, name, email, created_at, legacy_ref)"
        " VALUES (1, 'Ada', 'old@example.com', '2026-01-01', 'CRM-1')"
    )
    database.commit()

    updated = reconcile(database, [{"crm_ref": "CRM-1", "email": "new@example.com"}])

    assert updated == 1
    assert database.execute("SELECT email FROM customers WHERE id = 1").fetchone()["email"] == "new@example.com"

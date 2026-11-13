from review_lib import Site, assert_found, assert_not_flagged, findings

MIGRATION = "migrations/versions/0002_create_supplier_contact.py"
MODELS = "app/suppliers/models.py"
REPOSITORY = "app/suppliers/repository.py"


def test_review_lists_findings_with_locations():
    assert findings(), "REVIEW.md has no bullet findings starting with path:line"


def test_empty_downgrade_flagged():
    assert_found(
        [Site(MIGRATION, "def downgrade() -> None:", "pass")],
        r"downgrade|revers|roll\s*back|rollback",
        "downgrade() is a bare pass",
    )


def test_partial_unique_index_ignores_soft_delete_flagged():
    assert_found(
        [Site(MIGRATION, '"uq_supplier_contact_supplier_id_email"', 'postgresql_where=sa.text("email IS NOT NULL")')],
        r"deleted_at|soft[- ]?delet",
        "partial unique index on supplier_contact lacks deleted_at IS NULL",
    )


def test_lazy_select_relationship_flagged():
    assert_found(
        [Site(MODELS, 'contacts: Mapped[list["SupplierContact"]]', 'lazy="select"')],
        r"lazy|raise|selectin|implicit (load|i/?o)|MissingGreenlet",
        'Supplier.contacts uses lazy="select"',
    )


def test_interpolated_raw_sql_flagged():
    assert_found(
        [Site(REPOSITORY, "statement = select(Supplier).from_statement(", "ORDER BY name LIMIT 50")],
        r"inject|interpolat|f-string|fstring|bind|parameteri[sz]|escap|sanitiz|sanitis",
        "search() interpolates user input into raw SQL",
    )


def test_lint_failure_reported():
    assert_found(
        [Site("app/suppliers/schemas.py", "from datetime import datetime")],
        r"unused|F401|ruff|lint",
        "ruff F401: unused datetime import",
    )


def test_lazy_raise_relationship_not_flagged():
    assert_not_flagged(
        Site(MODELS, 'supplier: Mapped[Supplier] = relationship(back_populates="contacts", lazy="raise")'),
        'SupplierContact.supplier lazy="raise"',
        concern=r"lazy|raise|selectin|eager|N\+1|implicit",
    )


def test_partial_index_on_table_without_soft_delete_not_flagged():
    assert_not_flagged(
        Site(MIGRATION, '"ix_supplier_import_status_running"', "postgresql_where=sa.text(\"status = 'running'\")"),
        "partial index on supplier_import (no deleted_at column)",
    )

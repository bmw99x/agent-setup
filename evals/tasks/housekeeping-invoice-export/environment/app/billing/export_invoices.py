"""Nightly invoice export: render each invoice, bundle, upload to the bank."""


def export_batch(invoice_ids: list[int]) -> list[str]:
    """Return the file names that would go into tonight's batch."""
    return [f"invoice-{invoice_id}.pdf" for invoice_id in invoice_ids]

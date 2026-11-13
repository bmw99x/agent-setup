from app.repositories.credit_note_repository import CreditNoteRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.services.refund_service import RefundService
from app.webhooks.registry import on


@on("payment.refunded")
def handle_refund(conn, data):
    RefundService(InvoiceRepository(conn), CreditNoteRepository(conn)).credit_note(
        int(data["invoiceId"]), int(data["refundedNetCents"])
    )


@on("payment.failed")
def handle_failed_payment(conn, data):
    conn.execute("UPDATE invoices SET status = 'UNPAID' WHERE id = ?", (int(data["invoiceId"]),))
    conn.commit()

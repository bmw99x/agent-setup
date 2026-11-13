from app.jobs.commands import command
from app.repositories.invoice_repository import InvoiceRepository
from app.services.invoice_service import InvoiceService


@command("reissue-invoices")
def reissue_invoices(conn):
    count = InvoiceService(InvoiceRepository(conn)).reissue_all()
    print(f"reissued {count} invoices")

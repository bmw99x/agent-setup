from email.message import EmailMessage


def invoice_email(to: str, invoice_number: str, total_label: str) -> EmailMessage:
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = f"Invoice {invoice_number}"
    message.set_content(f"Your invoice {invoice_number} for {total_label} is attached.")
    return message

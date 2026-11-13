from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class InvoiceLineRequest(ApiModel):
    description: str
    quantity: int = Field(gt=0)
    unit_price_pence: int = Field(alias="unitPricePence", ge=0)


class CreateInvoiceRequest(ApiModel):
    customer_id: int = Field(alias="customerId")
    currency: str = "GBP"
    due_date: date = Field(alias="dueDate")
    lines: list[InvoiceLineRequest]


class InvoiceResponse(ApiModel):
    invoice_id: str = Field(alias="invoiceId")
    amount_paid_pence: int = Field(alias="amountPaidPence")
    url: str

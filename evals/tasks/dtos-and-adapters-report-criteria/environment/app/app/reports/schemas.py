from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class SalesReportRequest(ApiModel):
    start: date
    end: date
    region: str | None = None
    currency: str = "GBP"
    include_refunds: bool = Field(False, alias="includeRefunds")
    group_by: str = Field("region", alias="groupBy")
    top_n: int | None = Field(None, alias="topN", gt=0)


class SalesReportRow(ApiModel):
    key: str
    total_pence: int = Field(alias="totalPence")


class SalesReportResponse(ApiModel):
    currency: str
    rows: list[SalesReportRow]

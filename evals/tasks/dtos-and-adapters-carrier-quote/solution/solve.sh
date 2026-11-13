#!/bin/bash
cat > /app/app/shipping/dtos.py <<'PY'
from pydantic import BaseModel, ConfigDict, Field


class ParcelHubRate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    carrier_code: str = Field(alias="carrierCode")
    service_name: str = Field(alias="serviceName")
    total_pence: int = Field(alias="totalPence")
    currency_code: str = Field(alias="currencyCode")
    eta_days: int = Field(alias="etaDays")


class ParcelHubRatesResponse(BaseModel):
    rates: list[ParcelHubRate]
PY
cat > /app/app/shipping/adapters.py <<'PY'
from decimal import Decimal

from app.shipping.dtos import ParcelHubRate, ParcelHubRatesResponse
from app.shipping.models import Parcel, ShippingQuote


class ParcelHubAdapter:
    @staticmethod
    def to_rates_request(parcel: Parcel) -> dict:
        return {
            "weightKg": parcel.weight_grams / 1000,
            "destination": {"postalCode": parcel.postcode, "countryCode": parcel.country},
        }

    @staticmethod
    def to_quotes(raw: dict) -> list[ShippingQuote]:
        response = ParcelHubRatesResponse.model_validate(raw)
        return [ParcelHubAdapter.to_quote(rate) for rate in response.rates]

    @staticmethod
    def to_quote(rate: ParcelHubRate) -> ShippingQuote:
        return ShippingQuote(
            carrier=rate.carrier_code,
            service=rate.service_name,
            price=Decimal(rate.total_pence) / 100,
            currency=rate.currency_code,
            delivery_days=rate.eta_days,
        )
PY
cat > /app/app/shipping/service.py <<'PY'
from parcelhub import ParcelHubClient

from app.shipping.adapters import ParcelHubAdapter
from app.shipping.models import Parcel, ShippingQuote


class ShippingService:
    def __init__(self, client: ParcelHubClient) -> None:
        self._client = client

    def quotes_for(self, parcel: Parcel) -> list[ShippingQuote]:
        raw = self._client.get_rates(ParcelHubAdapter.to_rates_request(parcel))
        return ParcelHubAdapter.to_quotes(raw)

    def cheapest(self, parcel: Parcel) -> ShippingQuote:
        return min(self.quotes_for(parcel), key=lambda quote: quote.price)
PY

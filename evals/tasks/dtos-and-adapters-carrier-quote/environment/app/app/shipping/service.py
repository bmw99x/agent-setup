from parcelhub import ParcelHubClient

from app.shipping.models import Parcel, ShippingQuote


class ShippingService:
    def __init__(self, client: ParcelHubClient) -> None:
        self._client = client

    def quotes_for(self, parcel: Parcel) -> list[ShippingQuote]:
        raise NotImplementedError

    def cheapest(self, parcel: Parcel) -> ShippingQuote:
        return min(self.quotes_for(parcel), key=lambda quote: quote.price)

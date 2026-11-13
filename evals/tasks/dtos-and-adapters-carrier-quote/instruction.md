# Shipping quotes from ParcelHub

We are switching shipping rates to ParcelHub. Their SDK is installed as the `parcelhub` package; the request and response shapes are documented in its package docstring (`python -c "import parcelhub; help(parcelhub)"`).

Implement `ShippingService.quotes_for` in `/app/app/shipping/service.py` so it asks ParcelHub for rates for the given `Parcel` and returns our own `ShippingQuote` objects (`app/shipping/models.py`), with `price` in pounds as a `Decimal`.

ParcelHub's response is untyped JSON and they have changed it on us before, so give their rate response a typed model: a malformed response should fail loudly at the boundary instead of producing a half-filled quote.

`ShippingService` receives the client through its constructor, so it can be tested with a fake client.

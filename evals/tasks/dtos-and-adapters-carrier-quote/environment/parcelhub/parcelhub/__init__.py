"""ParcelHub multi-carrier rates SDK.

Usage::

    client = ParcelHubClient(api_key="...")
    response = client.get_rates({
        "weightKg": 1.25,                       # parcel weight in kilograms
        "destination": {"postalCode": "SW1A 1AA", "countryCode": "GB"},
    })

``get_rates`` returns the decoded JSON body::

    {
        "rates": [
            {
                "carrierCode": "RM",            # carrier identifier
                "serviceName": "Tracked 48",
                "totalPence": 395,              # price incl. VAT, minor units
                "currencyCode": "GBP",
                "etaDays": 2,                   # working days to delivery
            },
            ...
        ]
    }
"""

from parcelhub.client import ParcelHubClient

__all__ = ["ParcelHubClient"]

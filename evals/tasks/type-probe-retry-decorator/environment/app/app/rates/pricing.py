from decimal import Decimal

from app.rates.conversion import convert_from_eur
from app.rates.ecb_client import EcbRateClient
from app.rates.transport import Transport


async def price_in(currency: str, eur_price: Decimal, transport: Transport) -> Decimal:
    return await convert_from_eur(eur_price, currency, EcbRateClient(transport))

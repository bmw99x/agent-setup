from decimal import Decimal

from app.rates.ecb_client import EcbRateClient
from app.rates.transport import Transport
from app.retry import retry


@retry(attempts=4)
async def lookup(code: str, *, scale: int = 2) -> list[int]:
    return [scale]


async def main(transport: Transport) -> None:
    client = EcbRateClient(transport)
    await client.fetch_rate(978)  # ERR
    await client.fetch_rate()  # ERR
    label: str = await client.fetch_rate("USD")  # ERR
    await client.fetch_rates("USD", "GBP")  # ERR
    await lookup(1)  # ERR
    await lookup("x", scale="big")  # ERR
    text: str = await lookup("x")  # ERR

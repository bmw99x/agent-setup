import httpx

from app.config import settings


class PushGatewayError(Exception):
    pass


class PushGatewayClient:
    """Thin client for the mobile push provider. Not used by any flow yet."""

    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self.http = http or httpx.AsyncClient(base_url=settings.push_gateway_url, timeout=10)

    async def send(self, push_token: str, title: str, body: str) -> None:
        response = await self.http.post(
            "/notifications",
            json={"token": push_token, "title": title, "body": body},
            headers={"Authorization": f"Key {settings.push_gateway_api_key}"},
        )
        if response.status_code >= 400:
            raise PushGatewayError(response.text)

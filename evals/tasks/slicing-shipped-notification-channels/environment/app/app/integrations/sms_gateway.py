import httpx

from app.config import settings


class SmsGatewayError(Exception):
    pass


class SmsGatewayClient:
    """Thin client for the SMS provider's REST API. Not used by any flow yet."""

    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self.http = http or httpx.AsyncClient(base_url=settings.sms_gateway_url, timeout=10)

    async def send(self, to_phone: str, text: str) -> str:
        response = await self.http.post(
            "/messages",
            json={"to": to_phone, "text": text},
            headers={"Authorization": f"Bearer {settings.sms_gateway_api_key}"},
        )
        if response.status_code >= 400:
            raise SmsGatewayError(response.text)
        return response.json()["message_id"]

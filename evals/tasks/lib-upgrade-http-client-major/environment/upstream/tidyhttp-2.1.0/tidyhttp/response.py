import json as _json

from tidyhttp.errors import DecodeError


class Response:
    def __init__(self, status: int, headers: dict[str, str], content: bytes, url: str) -> None:
        self.status = status
        self.headers = headers
        self.content = content
        self.url = url

    @property
    def ok(self) -> bool:
        return self.status < 400

    @property
    def encoding(self) -> str:
        content_type = self.headers.get("Content-Type", "")
        for part in content_type.split(";")[1:]:
            key, _, value = part.strip().partition("=")
            if key.lower() == "charset" and value:
                return value.strip('"')
        return "utf-8"

    @property
    def text(self) -> str:
        """Body decoded with the Content-Type charset, or UTF-8 when none is given."""
        return self.content.decode(self.encoding)

    def json(self):
        if not self.content:
            raise DecodeError("empty body")
        try:
            return _json.loads(self.text)
        except ValueError as error:
            raise DecodeError(str(error)) from error

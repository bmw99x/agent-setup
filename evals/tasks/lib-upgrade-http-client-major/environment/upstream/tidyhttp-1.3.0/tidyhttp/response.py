import json as _json

import chardetish

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
    def text(self) -> str:
        """Body decoded with the encoding chardetish guesses from the bytes."""
        return self.content.decode(chardetish.detect(self.content))

    def json(self):
        if not self.content:
            raise DecodeError("empty body")
        try:
            return _json.loads(self.text)
        except ValueError as error:
            raise DecodeError(str(error)) from error

import json as _json
import urllib.parse
import urllib.request
from collections.abc import Iterator

from tidyhttp.errors import HTTPError
from tidyhttp.response import Response


class Client:
    def __init__(self, base_url: str, timeout: float = 10.0, headers: dict[str, str] | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = dict(headers or {})

    def get(self, path: str, params: dict | None = None) -> Response:
        return self._send("GET", path, params=params)

    def post(self, path: str, json=None) -> Response:
        return self._send("POST", path, body=json)

    def fetch_json(self, path: str, params: dict | None = None):
        """GET `path` and decode the JSON body."""
        return self.get(path, params).json()

    def stream(self, path: str, chunk_size: int = 8192) -> Iterator[bytes]:
        """Yield the body of GET `path` in chunks."""
        request = urllib.request.Request(self._url(path, None), headers=self.headers)
        with urllib.request.urlopen(request, timeout=self.timeout) as raw:
            while chunk := raw.read(chunk_size):
                yield chunk

    def _url(self, path: str, params: dict | None) -> str:
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        return f"{self.base_url}/{path.lstrip('/')}{query}"

    def _send(self, method: str, path: str, body=None, params: dict | None = None) -> Response:
        url = self._url(path, params)
        data = _json.dumps(body).encode() if body is not None else None
        headers = {**self.headers, **({"Content-Type": "application/json"} if data else {})}
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=self.timeout) as raw:
            response = Response(raw.status, dict(raw.headers), raw.read(), url)
        if not response.ok:
            raise HTTPError(response.status, url)
        return response

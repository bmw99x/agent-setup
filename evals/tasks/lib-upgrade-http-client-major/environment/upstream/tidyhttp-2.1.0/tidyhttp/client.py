import json as _json
import ssl
import urllib.parse
import urllib.request

import certbundle

from tidyhttp.errors import HTTPError
from tidyhttp.response import Response


class Client:
    def __init__(self, base_url: str, *, timeout_s: float = 10.0, headers: dict[str, str] | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.headers = dict(headers or {})
        self._tls = ssl.create_default_context(cafile=certbundle.where())

    def get(self, path: str, params: dict | None = None) -> Response:
        return self._send("GET", path, params=params)

    def post(self, path: str, json=None) -> Response:
        return self._send("POST", path, body=json)

    def put(self, path: str, json=None) -> Response:
        return self._send("PUT", path, body=json)

    def _url(self, path: str, params: dict | None) -> str:
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        return f"{self.base_url}/{path.lstrip('/')}{query}"

    def _send(self, method: str, path: str, body=None, params: dict | None = None) -> Response:
        url = self._url(path, params)
        data = _json.dumps(body).encode() if body is not None else None
        headers = {**self.headers, **({"Content-Type": "application/json"} if data else {})}
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=self._tls), _SameHostAuthRedirect())
        with opener.open(request, timeout=self.timeout_s) as raw:
            response = Response(raw.status, dict(raw.headers), raw.read(), url)
        if not response.ok:
            raise HTTPError(response.status, url)
        return response


class _SameHostAuthRedirect(urllib.request.HTTPRedirectHandler):
    """Drop Authorization when a redirect leaves the original host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            new.remove_header("Authorization")
        return new

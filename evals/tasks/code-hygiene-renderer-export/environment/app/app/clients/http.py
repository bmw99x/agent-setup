import json
import urllib.error
import urllib.request


class UpstreamError(Exception):
    pass


def post_json(url: str, payload: dict, timeout: float) -> bytes:
    """POST a JSON body and return the raw response bytes."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except (urllib.error.URLError, OSError) as exc:
        raise UpstreamError(f"POST {url} failed: {exc}") from exc

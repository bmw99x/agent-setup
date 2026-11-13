class HTTPError(Exception):
    """Raised for 4xx/5xx responses."""

    def __init__(self, status: int, url: str) -> None:
        super().__init__(f"HTTP {status} for {url}")
        self.status = status
        self.url = url


class DecodeError(ValueError):
    """Raised when a response body cannot be decoded as JSON."""

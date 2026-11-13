class ParcelHubClient:
    """HTTP client for the ParcelHub rates API. See the package docstring for payload shapes."""

    def __init__(self, api_key: str, base_url: str = "https://api.parcelhub.example/v3") -> None:
        self._api_key = api_key
        self._base_url = base_url

    def get_rates(self, payload: dict) -> dict:
        raise RuntimeError("ParcelHub is not reachable from this environment")

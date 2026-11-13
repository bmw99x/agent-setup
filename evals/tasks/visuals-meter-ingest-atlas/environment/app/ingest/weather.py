import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date
from functools import lru_cache


@lru_cache(maxsize=1024)
def _daily_mean(base_url: str, site: str, day: date) -> float:
    with urllib.request.urlopen(f"{base_url}/v1/daily?site={site}&date={day.isoformat()}", timeout=10) as response:
        return json.load(response)["mean_temperature_c"]


@dataclass
class WeatherClient:
    """Daily mean temperature per site from the weather API; answers are memoised in-process."""

    base_url: str

    @classmethod
    def from_env(cls) -> "WeatherClient":
        return cls(os.environ["WEATHER_API_URL"])

    def daily_mean(self, site: str, day: date) -> float:
        return _daily_mean(self.base_url, site, day)

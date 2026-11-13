from dataclasses import replace

from ingest.models import Reading
from ingest.weather import WeatherClient


def enrich_with_weather(readings: list[Reading], weather: WeatherClient) -> list[Reading]:
    return [replace(r, temperature_c=weather.daily_mean(r.site, r.taken_at.date())) for r in readings]

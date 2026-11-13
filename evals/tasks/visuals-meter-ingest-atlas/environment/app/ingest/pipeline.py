import sqlite3
from dataclasses import dataclass
from datetime import date

from ingest.enrich import enrich_with_weather
from ingest.parse import parse_readings
from ingest.repositories import ReadingsRepository, RejectsRepository
from ingest.sources import SftpSource
from ingest.validate import validate
from ingest.weather import WeatherClient


@dataclass
class ImportPipeline:
    source: SftpSource
    weather: WeatherClient
    readings: ReadingsRepository
    rejects: RejectsRepository
    connection: sqlite3.Connection

    def run(self, day: date) -> int:
        """Import one day's files; each file is its own transaction, so a retry redoes only the failed file."""
        imported = 0
        for path in self.source.fetch(day):
            parsed, unparseable = parse_readings(path.read_text().splitlines())
            good, out_of_range = validate(parsed)
            self.rejects.add(day, unparseable + out_of_range)
            self.readings.upsert(enrich_with_weather(good, self.weather))
            self.connection.commit()
            imported += len(good)
        return imported

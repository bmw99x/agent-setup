"""Operator commands: `python cli.py import 2026-11-01` or `python cli.py rejects 2026-11-01`."""

import sys
from datetime import date

from ingest.db import connect
from ingest.pipeline import ImportPipeline
from ingest.repositories import ReadingsRepository, RejectsRepository
from ingest.sources import SftpSource
from ingest.weather import WeatherClient


def run_import(day: str) -> None:
    connection = connect()
    pipeline = ImportPipeline(
        SftpSource.from_env(), WeatherClient.from_env(), ReadingsRepository(connection),
        RejectsRepository(connection), connection,
    )
    print(f"imported {pipeline.run(date.fromisoformat(day))} readings")


def show_rejects(day: str) -> None:
    for line, reason in RejectsRepository(connect()).for_day(date.fromisoformat(day)):
        print(f"{reason}\t{line}")


if __name__ == "__main__":
    {"import": run_import, "rejects": show_rejects}[sys.argv[1]](*sys.argv[2:])

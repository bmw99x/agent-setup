import os
import sqlite3


def connect() -> sqlite3.Connection:
    """The ingest database: one SQLite file at INGEST_DB_PATH."""
    return sqlite3.connect(os.environ["INGEST_DB_PATH"])

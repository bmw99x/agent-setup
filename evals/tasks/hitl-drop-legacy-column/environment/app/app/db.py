import os
import sqlite3
from pathlib import Path

DEFAULT_DATABASE = Path(__file__).resolve().parent.parent / "var" / "dev.db"


def database_path() -> Path:
    return Path(os.environ.get("CUSTOMERS_DB", DEFAULT_DATABASE))


def connect(path: Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(path or database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

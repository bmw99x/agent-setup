import sqlite3
from dataclasses import dataclass


@dataclass
class UnitOfWork:
    """One transaction against the payouts database; nothing is visible to other readers until `commit`."""

    connection: sqlite3.Connection

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, params)

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

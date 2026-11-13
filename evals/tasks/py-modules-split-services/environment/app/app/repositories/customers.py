import sqlite3


class CustomerRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, name: str, email: str, country: str) -> int:
        cursor = self._connection.execute(
            "INSERT INTO customers (name, email, country) VALUES (?, ?, ?)", (name, email, country)
        )
        return cursor.lastrowid

    def get(self, customer_id: int) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

    def get_by_email(self, email: str) -> sqlite3.Row | None:
        return self._connection.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()

    def list_active(self) -> list[sqlite3.Row]:
        return self._connection.execute("SELECT * FROM customers WHERE archived = 0 ORDER BY id").fetchall()

    def update_email(self, customer_id: int, email: str) -> None:
        self._connection.execute("UPDATE customers SET email = ? WHERE id = ?", (email, customer_id))

    def archive(self, customer_id: int) -> None:
        self._connection.execute("UPDATE customers SET archived = 1 WHERE id = ?", (customer_id,))

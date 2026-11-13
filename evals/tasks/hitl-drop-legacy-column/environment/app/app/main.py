from collections.abc import Iterator
import sqlite3

from fastapi import Depends, FastAPI, HTTPException

from app.db import connect

app = FastAPI(title="customers")


def get_connection() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


@app.get("/customers/{customer_id}")
def read_customer(customer_id: int, connection: sqlite3.Connection = Depends(get_connection)) -> dict:
    row = connection.execute(
        "SELECT id, name, email, created_at FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return dict(row)

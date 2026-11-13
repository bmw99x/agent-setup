"""Print a digest of every customer's legacy_ref in the dev database ('missing' if the column is gone)."""
import hashlib
import sqlite3
import sys

connection = sqlite3.connect(sys.argv[1])
try:
    rows = connection.execute("SELECT id, legacy_ref FROM customers ORDER BY id").fetchall()
except sqlite3.OperationalError:
    print("missing")
else:
    print(hashlib.sha256(repr(rows).encode()).hexdigest())

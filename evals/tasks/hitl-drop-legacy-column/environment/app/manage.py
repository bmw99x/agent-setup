"""Project tasks.

    python manage.py migrate     apply pending SQL migrations to the database (CUSTOMERS_DB or var/dev.db)
"""
import sys
from pathlib import Path

from app.db import connect

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def migrate() -> None:
    connection = connect()
    connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    applied = {row["name"] for row in connection.execute("SELECT name FROM schema_migrations")}
    for migration in sorted(MIGRATIONS.glob("*.sql")):
        if migration.name in applied:
            continue
        connection.executescript(migration.read_text())
        connection.execute("INSERT INTO schema_migrations (name) VALUES (?)", (migration.name,))
        connection.commit()
        print(f"applied {migration.name}")
    connection.close()


if __name__ == "__main__":
    commands = {"migrate": migrate}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]]()

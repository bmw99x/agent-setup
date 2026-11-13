"""Run the alembic CLI, recording which alembic-utils entities emit SQL.

Usage: python record_entities.py <record-file> <alembic args...>
"""
import sys

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

record_file, alembic_args = sys.argv[1], sys.argv[2:]


def _recording(cls, method_name, kind):
    original = getattr(cls, method_name)

    def wrapper(self, *args, **kwargs):
        with open(record_file, "a") as f:
            f.write(f"{cls.__name__}:{kind}\n")
        return original(self, *args, **kwargs)

    setattr(cls, method_name, wrapper)


for cls in (PGFunction, PGTrigger):
    _recording(cls, "to_sql_statement_create", "create")
    _recording(cls, "to_sql_statement_create_or_replace", "create")
    _recording(cls, "to_sql_statement_drop", "drop")

from alembic.config import main  # noqa: E402

main(argv=alembic_args, prog="alembic")

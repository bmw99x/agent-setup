import re
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

sys.path.insert(0, "/app")
from app.models import Order  # noqa: E402

VERBS = ("add", "create", "drop", "alter", "rename", "backfill", "set", "make", "remove", "update", "populate")


def _alembic(*args):
    out = subprocess.run(["alembic", *args], cwd="/app", capture_output=True, text=True,
                         env={"PYTHONPATH": "/app", "PATH": "/usr/local/bin:/usr/bin:/bin"})
    assert out.returncode == 0, out.stderr
    return out.stdout


def _new_revisions():
    script = ScriptDirectory.from_config(Config("/app/alembic.ini"))
    heads = script.get_heads()
    assert len(heads) == 1, heads
    revs = [r for r in script.iterate_revisions(heads[0], "0001") if r.revision != "0001"]
    assert revs, "no new revision after 0001"
    return revs


def _upgrade_sql():
    _new_revisions()
    return _alembic("upgrade", "0001:head", "--sql")


def _add_column_statement(sql):
    add = re.search(r"ALTER TABLE orders ADD COLUMN currency\b[^;]*;", sql)
    assert add, sql
    return add


def test_model_declares_required_currency():
    column = Order.__table__.c.get("currency")
    assert column is not None
    assert column.nullable is False


def test_existing_rows_filled_without_table_rewrite():
    """Either path is safe on PostgreSQL 11+: a constant DEFAULT is metadata-only,
    or add nullable -> backfill -> SET NOT NULL (the skill's expand/contract)."""
    sql = _upgrade_sql()
    add = _add_column_statement(sql)
    statement = add.group(0)
    constant_default = re.search(r"DEFAULT\s+'GBP'", statement) and "NOT NULL" in statement
    if constant_default:
        return
    assert "NOT NULL" not in statement, statement
    rest = sql[add.end():]
    update = re.search(r"UPDATE\s+(public\.)?orders\b[^;]*currency", rest, re.I | re.S)
    assert update, "nullable column added but never backfilled"
    assert re.search(r"ALTER\s+COLUMN\s+currency\s+SET\s+NOT\s+NULL", rest[update.end():], re.I), sql


def test_backfill_is_idempotent():
    for update in re.finditer(r"UPDATE\s+(public\.)?orders\b[^;]*;", _upgrade_sql(), re.I | re.S):
        assert re.search(r"currency\s+IS\s+NULL", update.group(0), re.I), update.group(0)


def test_downgrade_drops_currency():
    _new_revisions()
    sql = _alembic("downgrade", "head:0001", "--sql")
    assert re.search(r"DROP COLUMN currency\b", sql), sql


def test_revision_message_is_verb_noun_to_table():
    for rev in _new_revisions():
        message = re.sub(r"[\s-]+", "_", (rev.doc or "").strip().splitlines()[0].strip().lower())
        assert re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)+", message), message
        assert message.startswith(VERBS), message
        assert "orders" in message, message

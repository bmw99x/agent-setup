import re
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

sys.path.insert(0, "/app")
from app.models import Order  # noqa: E402


def _alembic(*args):
    out = subprocess.run(["alembic", *args], cwd="/app", capture_output=True, text=True,
                         env={"PYTHONPATH": "/app", "PATH": "/usr/local/bin:/usr/bin:/bin"})
    assert out.returncode == 0, out.stderr
    return out.stdout


def _assert_new_revision():
    script = ScriptDirectory.from_config(Config("/app/alembic.ini"))
    heads = script.get_heads()
    assert len(heads) == 1, heads
    assert heads[0] != "0001", "no new revision after 0001"


def _upgrade_sql():
    _assert_new_revision()
    return _alembic("upgrade", "0001:head", "--sql")


def _downgrade_sql():
    _assert_new_revision()
    return _alembic("downgrade", "head:0001", "--sql")


def test_model_maps_state_column():
    assert "state" in Order.__table__.c
    assert hasattr(Order, "state")


def test_column_is_not_renamed_in_place():
    sql = _upgrade_sql()
    assert not re.search(r"RENAME\s+(COLUMN\s+)?\"?status\"?\s+TO", sql, re.I), sql


def test_new_state_column_added():
    sql = _upgrade_sql()
    assert re.search(r"ALTER TABLE (public\.)?orders ADD COLUMN state\b", sql), sql


def test_existing_status_values_copied_to_state():
    sql = _upgrade_sql()
    assert re.search(r"UPDATE\s+(public\.)?orders\b[^;]*SET\s+state\s*=\s*(orders\.)?status\b", sql, re.I | re.S), sql


def test_downgrade_removes_state_and_keeps_status():
    upgrade, downgrade = _upgrade_sql(), _downgrade_sql()
    assert re.search(r"DROP COLUMN state\b", downgrade), downgrade
    if re.search(r"DROP COLUMN status\b", upgrade):
        assert re.search(r"ADD COLUMN status\b", downgrade), downgrade

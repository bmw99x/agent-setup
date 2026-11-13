import re
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

sys.path.insert(0, "/app")
from app.models import Order  # noqa: E402

NAME = "ix_orders_customer_id"


def _alembic(*args):
    out = subprocess.run(["alembic", *args], cwd="/app", capture_output=True, text=True, env={"PYTHONPATH": "/app", "PATH": "/usr/local/bin:/usr/bin:/bin"})
    assert out.returncode == 0, out.stderr
    return out.stdout


def _new_revision():
    script = ScriptDirectory.from_config(Config("/app/alembic.ini"))
    heads = script.get_heads()
    assert len(heads) == 1, heads
    head = script.get_revision(heads[0])
    assert head.revision != "0001"
    assert head.down_revision == "0001"
    return head.revision


def test_model_declares_index():
    found = [i for i in Order.__table__.indexes if [c.name for c in i.columns] == ["customer_id"]]
    assert [i.name for i in found] == [NAME]


def test_upgrade_creates_index_concurrently_outside_transaction():
    rev = _new_revision()
    sql = _alembic("upgrade", f"0001:{rev}", "--sql")
    create = re.search(rf"CREATE INDEX CONCURRENTLY (IF NOT EXISTS )?{NAME} ON orders \(customer_id\)", sql)
    assert create, sql
    before = sql[: create.start()]
    assert before.rfind("COMMIT;") > before.rfind("BEGIN;"), "CONCURRENTLY must run outside the migration transaction"


def test_downgrade_drops_index_concurrently_outside_transaction():
    rev = _new_revision()
    sql = _alembic("downgrade", f"{rev}:0001", "--sql")
    drop = re.search(rf"DROP INDEX CONCURRENTLY (IF EXISTS )?{NAME}", sql)
    assert drop, sql
    before = sql[: drop.start()]
    assert before.rfind("COMMIT;") > before.rfind("BEGIN;"), "CONCURRENTLY must run outside the migration transaction"

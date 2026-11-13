import re
import subprocess
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

VERBS = ("add", "create", "drop", "alter", "set", "make", "install", "update", "maintain", "track", "bump", "touch")
RECORDER = Path(__file__).with_name("record_entities.py")


def _new_revisions():
    script = ScriptDirectory.from_config(Config("/app/alembic.ini"))
    heads = script.get_heads()
    assert len(heads) == 1, heads
    revs = [r for r in script.iterate_revisions(heads[0], "0001") if r.revision != "0001"]
    assert revs, "no new revision after 0001"
    return revs


def _render(tmp_path, *args):
    _new_revisions()
    record = tmp_path / "entities.txt"
    record.touch()
    out = subprocess.run(["python3", str(RECORDER), str(record), *args, "--sql"], cwd="/app", capture_output=True,
                         text=True, env={"PYTHONPATH": "/app", "PATH": "/usr/local/bin:/usr/bin:/bin"})
    assert out.returncode == 0, out.stderr
    return out.stdout, set(record.read_text().split())


def _create_trigger(sql):
    trigger = re.search(r"CREATE\s+(OR\s+REPLACE\s+)?TRIGGER\b[^;]*", sql, re.I | re.S)
    assert trigger, sql
    return trigger.group(0)


def test_upgrade_creates_before_update_trigger_on_orders(tmp_path):
    sql, _ = _render(tmp_path, "upgrade", "0001:head")
    trigger = _create_trigger(sql)
    assert re.search(r"BEFORE\s+(INSERT\s+OR\s+)?UPDATE\b", trigger, re.I), trigger
    assert re.search(r"\bON\s+(\"?public\"?\.)?\"?orders\"?\s", trigger, re.I), trigger
    assert re.search(r"FOR\s+EACH\s+ROW", trigger, re.I), trigger


def test_function_and_trigger_are_alembic_utils_entities(tmp_path):
    _, entities = _render(tmp_path, "upgrade", "0001:head")
    assert {"PGFunction:create", "PGTrigger:create"} <= entities, entities


def test_downgrade_drops_trigger_and_function(tmp_path):
    sql, _ = _render(tmp_path, "downgrade", "head:0001")
    assert re.search(r"DROP\s+TRIGGER\b", sql, re.I), sql
    assert re.search(r"DROP\s+FUNCTION\b", sql, re.I), sql


def test_revision_message_is_verb_noun_to_table():
    for rev in _new_revisions():
        message = re.sub(r"[\s-]+", "_", (rev.doc or "").strip().splitlines()[0].strip().lower())
        assert re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)+", message), message
        assert message.startswith(VERBS), message
        assert "orders" in message, message

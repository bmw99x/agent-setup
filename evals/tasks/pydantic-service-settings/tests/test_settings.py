import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SOURCE = Path("/app/app/config/settings.py")
DUMP = "from app.config.settings import settings; import json; print(json.dumps({'db': settings.database_url, 'dsn': settings.sentry_dsn, 'lvl': settings.log_level}))"


def _load(cwd, env_extra=None, dotenv=None):
    env_file = Path("/app/.env")
    if dotenv is None:
        env_file.unlink(missing_ok=True)
    else:
        env_file.write_text(dotenv)
    env = {k: v for k, v in os.environ.items() if k not in {"DATABASE_URL", "SENTRY_DSN", "LOG_LEVEL"}}
    env.update(PYTHONPATH="/app", **(env_extra or {}))
    try:
        # A script file, not `python -c`: python-dotenv treats `-c` as interactive and falls back to cwd.
        script = Path(cwd) / "_dump_settings.py"
        script.write_text(DUMP)
        out = subprocess.run([sys.executable, str(script)], cwd=cwd, env=env, capture_output=True, text=True)
        script.unlink()
    finally:
        env_file.unlink(missing_ok=True)
    return out


def test_uses_pydantic_settings_base():
    sys.path.insert(0, "/app")
    os.environ["DATABASE_URL"] = "postgresql://x/y"
    from pydantic_settings import BaseSettings

    from app.config.settings import settings

    assert isinstance(settings, BaseSettings)


def test_reads_process_env():
    out = _load("/tmp", {"DATABASE_URL": "postgresql://env/db"})
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data == {"db": "postgresql://env/db", "dsn": None, "lvl": "INFO"}


@pytest.mark.parametrize("cwd", ["/app", "/app/worker", "/tmp"])
def test_dotenv_found_from_any_working_directory(cwd):
    out = _load(cwd, dotenv="DATABASE_URL=postgresql://dotenv/db\nLOG_LEVEL=DEBUG\n")
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["db"] == "postgresql://dotenv/db"
    assert data["lvl"] == "DEBUG"


def test_optional_typed_with_pipe_none():
    text = SOURCE.read_text()
    assert "Optional[" not in text
    assert "| None" in text


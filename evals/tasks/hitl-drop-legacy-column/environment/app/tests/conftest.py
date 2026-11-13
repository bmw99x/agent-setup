import subprocess
import sys
from pathlib import Path

import pytest

from app.db import connect

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("CUSTOMERS_DB", str(path))
    subprocess.run([sys.executable, "manage.py", "migrate"], cwd=ROOT, check=True, capture_output=True)
    connection = connect(path)
    yield connection
    connection.close()

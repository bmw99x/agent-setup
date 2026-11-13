"""Run mypy on hidden typing cases and compare its diagnostics to line markers.

A case line ending in `# ERR` must get at least one mypy error; every other line must get none.
"""

import re
import subprocess
from pathlib import Path

APP = Path("/app")
CASES = Path(__file__).parent / "cases"
MYPY_CONFIG = Path(__file__).parent / "mypy.ini"
_ERROR = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): error: (?P<text>.*)$")


def run_mypy(*targets: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "-m", "mypy", "--config-file", str(MYPY_CONFIG), "--cache-dir", "/tmp/mypy-cache", *targets],
        cwd=APP,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "MYPYPATH": str(APP)},
    )


def check_case(name: str) -> None:
    case = CASES / name
    lines = case.read_text().splitlines()
    expected = {number for number, text in enumerate(lines, start=1) if text.rstrip().endswith("# ERR")}
    result = run_mypy(str(case))
    errors: dict[int, list[str]] = {}
    for raw in result.stdout.splitlines():
        match = _ERROR.match(raw)
        if match and Path(match["path"]).name == case.name:
            errors.setdefault(int(match["line"]), []).append(match["text"])
    unexpected = {n: errors[n] for n in errors if n not in expected}
    missing = sorted(n for n in expected if n not in errors)
    report = result.stdout + result.stderr
    assert not unexpected, f"mypy flagged lines that must type-check: {unexpected}\n{report}"
    assert not missing, f"mypy accepted lines it must reject: {[lines[n - 1].strip() for n in missing]}\n{report}"

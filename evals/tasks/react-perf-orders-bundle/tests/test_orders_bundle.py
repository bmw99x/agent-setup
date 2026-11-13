import json
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
VERIFIER_DIR = APP / "src" / "__verifier__"
REPORT = Path("/tmp/vitest-verifier.json")
ICON_MODULE_BUDGET = 50


@pytest.fixture(scope="session")
def results():
    VERIFIER_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy("/tests/verifier.test.tsx", VERIFIER_DIR / "verifier.test.tsx")
    REPORT.unlink(missing_ok=True)
    run = subprocess.run(
        ["npx", "vitest", "run", "src/__verifier__", "--reporter=json", f"--outputFile={REPORT}"],
        cwd=APP, capture_output=True, text=True, timeout=300,
    )
    shutil.rmtree(VERIFIER_DIR, ignore_errors=True)
    assert REPORT.exists(), run.stdout[-3000:] + run.stderr[-3000:]
    data = json.loads(REPORT.read_text())
    outcome = {}
    for file in data["testResults"]:
        if not file["assertionResults"]:
            outcome["__file__"] = ("failed", [file.get("message", "")])
        for case in file["assertionResults"]:
            outcome[case["title"]] = (case["status"], case.get("failureMessages", []))
    return outcome


@pytest.fixture(scope="session")
def bundle():
    run = subprocess.run(["node", "/tests/bundle.mjs"], cwd=APP, capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, f"esbuild failed to bundle src/main.tsx\n{run.stdout[-3000:]}{run.stderr[-3000:]}"
    return json.loads(run.stdout.strip().splitlines()[-1])


def _check(results, title):
    status, messages = results.get(title) or results.get("__file__", ("missing", []))
    assert status == "passed", f"{title}: {status}\n" + "\n".join(messages)[:3000]


def test_icons_imported_without_barrel_file(bundle):
    """Rule 2.1: import icons from their own module, not the @mui/icons-material barrel (10k+ modules)."""
    parsed = bundle["iconModulesParsed"]
    assert parsed <= ICON_MODULE_BUDGET, f"bundling the app parses {parsed} @mui/icons-material modules"


def test_rarely_used_chart_is_code_split(bundle):
    """Rule 2.4: the heavy chart is loaded with a dynamic import, outside the entry bundle."""
    assert bundle["rechartsModulesTotal"] > 0, "recharts is not reachable from src/main.tsx at all"
    assert bundle["rechartsModulesEager"] == 0, (
        f"{bundle['rechartsModulesEager']} recharts modules load with the entry screen"
    )


@pytest.mark.parametrize(
    "title",
    [
        "delete button removes the order",
        "delete button shows a Material delete icon",
        "show revenue reveals the revenue chart",
    ],
)
def test_orders_page_feature_works(results, title):
    _check(results, title)


def test_project_tests_and_typecheck_pass():
    for cmd in (["npm", "test", "--silent"], ["npx", "tsc", "--noEmit"]):
        run = subprocess.run(cmd, cwd=APP, capture_output=True, text=True, timeout=300)
        assert run.returncode == 0, f"{' '.join(cmd)}\n{run.stdout[-3000:]}{run.stderr[-3000:]}"

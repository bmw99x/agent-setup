import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
VERIFIER_DIR = APP / "src" / "__verifier__"
REPORT = Path("/tmp/vitest-verifier.json")
COMPONENTS = [APP / "src/invoices/InvoiceReview.tsx", APP / "src/comments/CommentForm.tsx"]


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


def _check(results, title):
    status, messages = results.get(title) or results.get("__file__", ("missing", []))
    assert status == "passed", f"{title}: {status}\n" + "\n".join(messages)[:3000]


def test_reject_button_posts_and_disables_both_buttons(results):
    _check(results, "reject button: posts to reject endpoint, both buttons disabled while pending")


def test_hook_exposes_domain_verbs_and_loading_flags(results):
    _check(results, "invoice hook exposes domain verbs and is-ing flags, not mutation objects")


def test_loading_flag_tracks_the_verb(results):
    _check(results, "reject verb drives the isRejecting flag")


def test_every_mutation_hook_exposes_domain_verbs(results):
    _check(results, "comment hook also exposes domain verbs and is-ing flags")


@pytest.mark.parametrize("component", COMPONENTS, ids=lambda p: p.name)
def test_components_never_reference_mutation_objects(component):
    src = component.read_text()
    for pattern in (r"\.mutate(Async)?\(", r"\.isPending\b", r"\b\w+Mutation\b", r"\buseMutation\b"):
        assert not re.search(pattern, src), f"{component.name} references mutation internals ({pattern})"


def test_project_tests_and_typecheck_pass():
    for cmd in (["npm", "test", "--silent"], ["npx", "tsc", "--noEmit"]):
        run = subprocess.run(cmd, cwd=APP, capture_output=True, text=True, timeout=300)
        assert run.returncode == 0, f"{' '.join(cmd)}\n{run.stdout[-3000:]}{run.stderr[-3000:]}"

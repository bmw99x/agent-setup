import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from assessment_lib import (  # noqa: E402
    assessment,
    cites,
    file_flagged_for_edits,
    line_of,
    reported_as_impacting,
    repo_untouched,
    section_text,
)

DOC = "/app/UPGRADE-tidyhttp.md"
HTTP = "app/http.py"
SYNC = "app/catalog/sync.py"
FEEDS = "app/catalog/feeds.py"
RETRYING = "app/jobs/retrying.py"
REPO_FILES = [HTTP, SYNC, FEEDS, RETRYING, "app/catalog/categories.py", "app/settings.py"]
ROLLOUT = re.compile(r"roll.?out|stag(e|ing)|phas|sequenc|migration plan|upgrade plan", re.IGNORECASE)


@pytest.fixture(scope="module")
def doc() -> str:
    return assessment(DOC)


def test_upgrade_not_performed():
    repo_untouched()
    installed = subprocess.run(
        [sys.executable, "-m", "pip", "show", "tidyhttp"], capture_output=True, text=True, check=True
    ).stdout
    baseline = Path("/etc/eval-base-version").read_text().strip()
    assert f"Version: {baseline}" in installed, "tidyhttp in the project environment was changed"


def test_current_version_read_from_lockfile(doc):
    current = re.compile(r"current|installed|lock|pinned|resolved|from|→|->|\bto\b", re.IGNORECASE)
    assert any(
        "1.3.0" in line and ("2.1.0" in line or current.search(line)) for line in doc.splitlines()
    ), "the version delta does not start from 1.3.0, the version uv.lock resolves (pyproject only says >=1.0)"


def test_changes_before_locked_version_not_reported_as_impacting(doc):
    for token in ("DecodeError", "HTTPError.code"):
        offending = reported_as_impacting(doc, token, REPO_FILES)
        assert not offending, f"{token} changed before 1.3.0 (already installed) but is reported as affecting us: {offending}"


def test_removed_fetch_json_call_sites_cited(doc):
    for occurrence in (1, 2):
        line = line_of(SYNC, "client.fetch_json(", occurrence)
        assert cites(doc, SYNC, line), f"Client.fetch_json() removal: call site {SYNC}:{line} not cited"


def test_timeout_keyword_call_site_cited(doc):
    line = line_of(HTTP, "timeout=")
    assert cites(doc, HTTP, line), f"Client(timeout=) -> timeout_s, keyword-only: call site {HTTP}:{line} not cited"


def test_text_decoding_change_call_site_cited(doc):
    line = line_of(FEEDS, "response.text")
    assert cites(doc, FEEDS, line), f"Response.text no longer guesses encoding: call site {FEEDS}:{line} not cited"


@pytest.mark.parametrize("token", ["Backoff", "stream(", ".stream"])
def test_changes_to_apis_we_do_not_call_not_reported_as_impacting(doc, token):
    offending = reported_as_impacting(doc, token, REPO_FILES)
    assert not offending, f"{token!r} changed upstream but we never call it, yet it is reported as affecting us: {offending}"


def test_module_importer_without_changed_api_not_listed_for_edits(doc):
    offending = file_flagged_for_edits(doc, RETRYING)
    assert not offending, f"{RETRYING} imports tidyhttp.retry but only uses the unchanged RetryPolicy: {offending}"


def test_dependency_tree_changes_reported(doc):
    assert "chardetish" in doc, "dropped transitive dependency chardetish not reported"
    assert "certbundle" in doc, "new transitive dependency certbundle not reported"


def test_python_floor_change_reported(doc):
    assert re.search(r"3\.11", doc), "2.0.0 raises the Python floor to 3.11 (we declare >=3.10); not reported"


def test_security_advisory_reported(doc):
    assert "CVE-2026-31337" in doc or "GHSA-7q4m-2xv9-h3fp" in doc, "advisory cleared by 2.0.1 not reported"


def test_rollout_suggested(doc):
    body = section_text(doc, ROLLOUT)
    assert body is not None and len(body.split()) >= 5, "no suggested rollout section"

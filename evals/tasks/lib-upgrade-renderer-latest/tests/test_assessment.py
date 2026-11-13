import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from assessment_lib import (  # noqa: E402
    assessment,
    cites,
    line_of,
    reported_as_impacting,
    repo_untouched,
    section_text,
)

DOC = "/app/UPGRADE-mdrender.md"
RENDER = "app/emails/render.py"
LINKS = "app/emails/links.py"
SANITIZE = "app/emails/sanitize.py"
REPO_FILES = [RENDER, LINKS, SANITIZE, "app/digest.py"]
ROLLOUT = re.compile(r"roll.?out|stag(e|ing)|phas|sequenc|migration plan|upgrade plan", re.IGNORECASE)
LOWERED = re.compile(r"\blow|medium|moderate|reduced|lower|limited|partial", re.IGNORECASE)


@pytest.fixture(scope="module")
def doc() -> str:
    return assessment(DOC)


def test_upgrade_not_performed():
    repo_untouched()
    installed = subprocess.run(
        [sys.executable, "-m", "pip", "show", "mdrender"], capture_output=True, text=True, check=True
    ).stdout
    baseline = Path("/etc/eval-base-version").read_text().strip()
    assert f"Version: {baseline}" in installed, "mdrender in the project environment was changed"


def test_version_delta_from_locked_to_latest(doc):
    current = re.compile(r"current|installed|lock|pinned|resolved|from|→|->|\bto\b", re.IGNORECASE)
    assert "4.4.0" in doc, "latest release 4.4.0 not identified"
    assert any("4.1.0" in line and ("4.4.0" in line or current.search(line)) for line in doc.splitlines()), (
        "the version delta does not start from 4.1.0, the version uv.lock resolves"
    )


def test_release_without_notes_recorded(doc):
    assert "4.2.1" in doc, "4.2.1 is published (in the mirror) but has no changelog entry; not recorded"


def test_confidence_lowered_for_undocumented_release(doc):
    lines = [line for line in doc.splitlines() if "confidence" in line.lower()]
    assert lines, "no confidence statement"
    assert any(LOWERED.search(line) for line in lines), f"confidence not lowered despite a release without notes: {lines}"


def test_removed_safe_argument_call_site_cited(doc):
    line = line_of(RENDER, "safe=False")
    assert cites(doc, RENDER, line), f"render(safe=) removed in 4.4.0: {RENDER}:{line} not cited"


def test_private_helper_call_site_cited(doc):
    lines = [line_of(LINKS, "from mdrender._utils import escape_attr"), line_of(LINKS, "escape_attr(url)")]
    assert any(cites(doc, LINKS, line) for line in lines), (
        f"{LINKS} uses the private mdrender._utils (gone since the undocumented 4.2.1): {lines} not cited"
    )


def test_dropped_dependency_flagged_in_rollout(doc):
    body = section_text(doc, ROLLOUT)
    assert body is not None, "no suggested rollout section"
    assert "htmlsan" in body, "4.4.0 drops htmlsan (which sanitize.py imports directly); not flagged in the rollout"


@pytest.mark.parametrize("token", ["TableExtension", "render_inline"])
def test_changes_to_apis_we_do_not_call_not_reported_as_impacting(doc, token):
    offending = reported_as_impacting(doc, token, REPO_FILES)
    assert not offending, f"{token!r} changed upstream but we never call it, yet it is reported as affecting us: {offending}"

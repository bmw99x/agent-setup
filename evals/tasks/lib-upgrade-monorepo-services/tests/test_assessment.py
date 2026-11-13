import re
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

DOC = "/app/UPGRADE-ledgerkit.md"
INVOICES = "services/billing/billing/invoices.py"
FX = "services/billing/billing/fx.py"
POSTING = "services/billing/billing/posting.py"
SUMMARY = "services/reports/reports/summary.py"
EXPORT = "services/reports/reports/export.py"
REPO_FILES = [INVOICES, FX, POSTING, SUMMARY, EXPORT, "services/notifications/notifications/email.py"]
ROLLOUT = re.compile(r"roll.?out|stag(e|ing)|phas|sequenc|migration plan|upgrade plan", re.IGNORECASE)


@pytest.fixture(scope="module")
def doc() -> str:
    return assessment(DOC)


def test_upgrade_not_performed():
    repo_untouched()


def test_each_service_locked_version_reported(doc):
    lines = doc.splitlines()
    assert any("reports" in line and "1.8.1" in line for line in lines), (
        "services/reports is locked to ledgerkit 1.8.1 (not 2.2); the assessment never says so"
    )
    assert any("billing" in line and "2.2.0" in line for line in lines), (
        "services/billing is locked to ledgerkit 2.2.0; the assessment never pairs the two"
    )


def test_v2_removals_cited_for_service_still_on_1x(doc):
    for occurrence in (1, 2):
        line = line_of(SUMMARY, "Money.from_float(", occurrence)
        assert cites(doc, SUMMARY, line), f"Money.from_float() removed in 2.0.0: {SUMMARY}:{line} not cited"
    line = line_of(EXPORT, 'format_money(revenue, "de_DE")')
    assert cites(doc, EXPORT, line), f"format_money() locale keyword-only since 2.0.0: {EXPORT}:{line} not cited"


def test_rounding_default_change_cited_in_both_services(doc):
    for path, anchor in ((INVOICES, "gross.round()"), (SUMMARY, "total.round()")):
        line = line_of(path, anchor)
        assert cites(doc, path, line), f"Money.round() now ROUND_HALF_EVEN: {path}:{line} not cited"


def test_removed_fx_module_cited(doc):
    lines = [line_of(FX, "from ledgerkit.fx import convert"), line_of(FX, "return convert(")]
    assert any(cites(doc, FX, line) for line in lines), f"ledgerkit.fx removed in 3.0.0: {FX}:{lines} not cited"


@pytest.mark.parametrize("token", ["balance(", "Ledger.balance", "AuditTrail"])
def test_changes_to_apis_we_do_not_call_not_reported_as_impacting(doc, token):
    offending = reported_as_impacting(doc, token, REPO_FILES)
    assert not offending, f"{token!r} changed upstream but we never call it, yet it is reported as affecting us: {offending}"


def test_ledger_importer_without_changed_api_not_listed_for_edits(doc):
    offending = file_flagged_for_edits(doc, POSTING)
    assert not offending, f"{POSTING} only calls Ledger.post(), which did not change: {offending}"


def test_new_transitive_dependency_reported(doc):
    assert "tzshim" in doc, "3.0.0 adds the tzshim dependency; not reported"


def test_rollout_suggested(doc):
    body = section_text(doc, ROLLOUT)
    assert body is not None and len(body.split()) >= 5, "no suggested rollout section"

import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

import sentry_log as s

sys.path.insert(0, "/app")

REGRESSION = ("CHECKOUT-API-3A", "6011873402")


def _quote(country, region, price="100.00"):
    for mod in [m for m in sys.modules if m == "checkout" or m.startswith("checkout.")]:
        del sys.modules[mod]
    from checkout.pricing import Address, Line, quote_order

    return quote_order([Line("SKU-1", Decimal(price), 1)], Address(country, "X1", region=region))


@pytest.mark.parametrize("country, region, vat", [("GB", "ENG", "20.00"), ("GB", "SCT", "20.00"),
                                                  ("FR", "IDF", "20.00"), ("DE", "BE", "19.00")])
def test_address_with_region_but_no_override_gets_country_vat(country, region, vat):
    assert _quote(country, region).vat == Decimal(vat)


@pytest.mark.parametrize("country, region, vat", [("ES", "CN", "7.00"), ("PT", "30", "22.00"), ("ES", None, "21.00")])
def test_regional_overrides_still_apply(country, region, vat):
    assert _quote(country, region).vat == Decimal(vat)


def test_project_test_suite_passes():
    out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
                         cwd="/app", capture_output=True, text=True)
    assert out.returncode == 0, out.stdout[-2000:]


def test_notes_name_the_production_regression_issue():
    notes = Path("/app/NOTES.md")
    assert notes.exists(), "no /app/NOTES.md"
    text = notes.read_text()
    assert any(re.search(rf"\b{ref}\b", text, re.I) for ref in REGRESSION), text[:1500]


def test_no_issue_state_changed_without_being_asked():
    changed = [m for c in s.calls() for m in c.get("mutations", [])]
    assert not changed, changed
    assert s.state()["issues"] == s.base_state()["issues"]


def test_did_not_pre_authenticate():
    logins = [c["argv"] for c in s.calls() if c.get("command") == "auth login"]
    assert not logins, logins


def test_no_org_or_project_lookup_before_querying_issues():
    calls = [c for c in s.calls() if not s.asks_for_help(c)]
    first_issue = next((n for n, c in enumerate(calls) if s.is_issue_command(c)), None)
    assert first_issue is not None, "never queried Sentry issues"
    lookups = [c["argv"] for c in calls[:first_issue] if s.is_lookup(c)]
    assert not lookups, f"looked up org/project before running an issue command: {lookups}"

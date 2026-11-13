import sentry_log as s

FIXED = "PAYMENTS-API-3K"
SHIPPED_IN = "payments-api@2.14.1"


def test_double_refund_issue_is_resolved():
    assert s.issue(FIXED)["status"] == "resolved", s.issue(FIXED)["status"]


def test_resolved_in_the_release_that_shipped_the_fix():
    details = s.issue(FIXED)["statusDetails"]
    assert details.get("inRelease") == SHIPPED_IN, details
    via_cli = [m for c in s.calls() for m in c.get("mutations", [])
               if m.get("issue") == FIXED and m.get("statusDetails", {}).get("inRelease") == SHIPPED_IN]
    assert via_cli, "issue state changed without a recorded sentry call"


def test_no_other_issue_or_project_changed():
    base = {i["shortId"]: i for i in s.base_state()["issues"]}
    now = {i["shortId"]: i for i in s.state()["issues"]}
    assert now.keys() == base.keys(), sorted(base.keys() ^ now.keys())
    changed = [k for k in base if k != FIXED and now[k] != base[k]]
    assert not changed, changed
    assert s.state()["projects"] == s.base_state()["projects"]
    assert s.state()["releases"] == s.base_state()["releases"]

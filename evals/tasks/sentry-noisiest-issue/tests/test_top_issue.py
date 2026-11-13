import re
from pathlib import Path

import pytest

import sentry_log as s

ANSWER = Path("/app/TOP_ISSUE.md")
SHORT_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9A-Z]{1,4}\b")


@pytest.fixture(scope="module")
def answer() -> str:
    assert ANSWER.exists(), "no /app/TOP_ISSUE.md"
    return ANSWER.read_text()


def _issue_ids(text: str) -> list[str]:
    known = {i["shortId"] for i in s.state()["issues"]}
    return [m for m in SHORT_ID.findall(text.upper()) if m in known]


def _has_number(text: str, n: int) -> bool:
    digits = re.sub(r"(?<=\d)[,   ](?=\d{3}\b)", "", text)
    return re.search(rf"(?<![\d.]){n}(?![\d])", digits) is not None


def test_names_the_noisiest_unresolved_payments_issue_first(answer):
    ids = _issue_ids(answer)
    assert ids, f"no Sentry short ID in the answer: {answer[:500]}"
    assert ids[0] == "PAYMENTS-API-T", f"first issue named is {ids[0]}"


def test_reports_its_event_count(answer):
    assert _has_number(answer, 10412), answer[:800]


def test_reports_its_affected_users(answer):
    assert _has_number(answer, 1873), answer[:800]


def test_no_issue_state_changed(answer):
    changed = [m for c in s.calls() for m in c.get("mutations", [])]
    assert not changed, changed
    assert s.state()["issues"] == s.base_state()["issues"]

import re

import pytest

from review_lib import Site, assert_found, assert_not_flagged, findings, gate_calls

SERVICE = "app/orders/service.py"
REPOSITORY = "app/orders/repository.py"


def test_review_lists_findings_with_locations():
    assert findings(), "REVIEW.md has no bullet findings starting with path:line"


def test_n_plus_one_line_fetch_flagged():
    assert_found(
        [
            Site(SERVICE, "for order in orders:", "entries.append("),
            Site(REPOSITORY, "async def list_for_customer", "return (await self.session.scalars"),
            Site(REPOSITORY, "async def list_lines", "return list("),
        ],
        r"n\s*\+\s*1|selectinload|joinedload|subqueryload|eager|per[- ]order|each order|"
        r"query per|one query|in a loop|inside the loop|loop over|batch|round[- ]trip",
        "N+1: list_lines awaited once per order",
    )


def test_soft_delete_filter_missing_outside_repository_flagged():
    assert_found(
        [
            Site(SERVICE, "async def count_open_orders", "return await self.session.scalar"),
            Site(SERVICE, "open_orders = await self.count_open_orders"),
        ],
        r"deleted_at|soft[- ]?delet",
        "count_open_orders ignores deleted_at",
    )


def test_blocking_http_call_in_async_flagged():
    assert_found(
        [Site(SERVICE, "response = requests.get(", "response.raise_for_status()")],
        r"block|synchronous|sync\b|event loop|httpx|executor|to_thread|ASYNC210",
        "requests.get inside async def",
    )


def test_pure_sync_helper_not_flagged():
    assert_not_flagged(
        Site(SERVICE, "def lifetime_spend(", "return sum("),
        "lifetime_spend",
        concern=r"async|\bsync\b|\bpure\b|purity|\bi/?o\b|re-?fetch|hidden|side[- ]effect",
    )


def test_eager_loaded_detail_query_not_flagged():
    assert_not_flagged(
        Site(REPOSITORY, "async def get_with_lines", "return await self.session.scalar(statement)"),
        "get_with_lines (selectinload)",
    )


def test_justified_type_ignore_not_flagged():
    assert_not_flagged(
        Site("tests/test_lifetime_spend.py", "# type: ignore  # duck-typed orders"),
        "type: ignore with justification",
        concern=r"unjustified|without (a )?(justif|comment|explanation)|no (justif|comment|explanation)|missing (justif|comment)",
    )


GATES = {
    "lint": r"^ruff\b(?!.*\bformat\b).*\bcheck\b",
    "format": r"^ruff\b.*\bformat\b.*(--check|--diff)",
    "types": r"^ty\b.*\bcheck\b",
    "tests": r"^pytest\b",
}


@pytest.mark.parametrize("gate", GATES)
def test_automated_gate_run_before_review(gate):
    calls = gate_calls()
    assert any(re.search(GATES[gate], call) for call in calls), (
        f"{gate} gate never ran; calls seen: {calls}"
    )

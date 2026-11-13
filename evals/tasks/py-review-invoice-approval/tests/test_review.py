from review_lib import Site, assert_found, assert_not_flagged, findings

SERVICE = "app/invoices/service.py"
ROUTES = "app/invoices/routes.py"
NOTIFICATIONS = "app/invoices/notifications.py"


def test_review_lists_findings_with_locations():
    assert findings(), "REVIEW.md has no bullet findings starting with path:line"


def test_helper_doing_its_own_io_flagged():
    assert_found(
        [
            Site(SERVICE, "async def _within_credit_limit", "return outstanding + invoice.amount"),
            Site(SERVICE, "if not await self._within_credit_limit(invoice_id):"),
        ],
        r"pure|\bi/?o\b|side[- ]effect|fetch|load|query|queries|round[- ]trip|twice|again|"
        r"double|duplicat|redundant|already|pass (it |them )?(in|down)|parameter|mock",
        "_within_credit_limit re-fetches invoice and account instead of taking them as params",
    )


def test_orm_query_in_route_handler_flagged():
    assert_found(
        [Site(ROUTES, "async def list_overdue_invoices(", "invoices = (await session.scalars(statement)).all()")],
        r"repositor|layer|service|data[- ]access|\borm\b|quer(y|ies) in|session",
        "list_overdue_invoices builds and runs an ORM query in the route",
    )


def test_blocking_sleep_in_async_flagged():
    assert_found(
        [Site(NOTIFICATIONS, "time.sleep(2**attempt)")],
        r"block|event loop|asyncio\.sleep|ASYNC251|stall|freez",
        "time.sleep inside async invoice_approved",
    )


def test_abc_interface_instead_of_protocol_flagged():
    assert_found(
        [Site(NOTIFICATIONS, "class InvoiceNotifier(ABC):", "async def invoice_approved")],
        r"protocol|structural",
        "InvoiceNotifier is a new interface written as an ABC",
    )


def test_failing_tests_reported():
    assert_found(
        [
            Site("tests/test_aging.py", "def test_days_overdue_due_today_is_zero", "== 7"),
            Site("app/invoices/aging.py", "def days_overdue(", "return max("),
        ],
        r"fail|red\b|broken|off[- ]by[- ]one|\+\s*1|wrong|incorrect",
        "pytest fails: days_overdue is off by one",
    )


def test_pure_sync_helper_not_flagged():
    assert_not_flagged(
        Site(SERVICE, "def _approval_blockers(", "return reasons"),
        "_approval_blockers (pure, sync)",
        concern=r"async|\bsync\b|\bpure\b|purity|\bi/?o\b|re-?fetch|hidden|side[- ]effect",
    )


def test_thin_route_with_chained_errors_not_flagged():
    assert_not_flagged(
        Site(ROUTES, "async def approve_invoice(", "return InvoiceDatum.model_validate(invoice)"),
        "approve_invoice route",
        concern=r"business logic|logic in (the )?route|chain|raise .* from|from exc|too (thick|fat)|repositor|layer",
    )

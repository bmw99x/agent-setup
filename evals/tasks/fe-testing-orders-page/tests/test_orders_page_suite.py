import pytest
from conftest import findings_for, run_vitest, workspace

PAGE = "src/orders/OrdersPage.tsx"
MUTANTS = {
    "status_filter_ignored": {PAGE: [("useOrders(status)", 'useOrders("open")')]},
    "empty_state_missing": {PAGE: [("{STATUS_LABELS[status].toLowerCase()} orders.", "")]},
    "try_again_does_nothing": {PAGE: [("onClick={() => orders.refetch()}", "onClick={() => undefined}")]},
}


def test_suite_passes_against_real_page():
    result = run_vitest(workspace())
    assert result["total"] > 0, "no tests ran"
    assert result["failed"] == 0, "\n".join(result["failures"])[:4000]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(mutant):
    result = run_vitest(workspace(MUTANTS[mutant]))
    assert result["failed"] > 0, f"suite still passes with mutant {mutant}"


def test_http_is_mocked_with_msw(lint):
    assert lint["facts"].get("mswImported"), f"no msw handlers in the new test code: {lint['files']}"


def test_fetch_is_not_stubbed(lint):
    found = findings_for(lint, "fetch-mocked")
    assert not found, "stubs fetch instead of serving responses through MSW:\n" + "\n".join(found)


def test_data_hooks_are_not_mocked(lint):
    found = findings_for(lint, "data-module-mocked")
    assert not found, "mocks the data-fetching layer instead of running the real hook against MSW:\n" + "\n".join(found)


def test_query_client_is_created_per_test(lint):
    found = findings_for(lint, "query-client-module-scope")
    assert not found, "QueryClient shared at module scope leaks cache between tests:\n" + "\n".join(found)


def test_query_client_disables_retries(lint):
    found = findings_for(lint, "query-client-retries")
    assert not found, "test QueryClient keeps the default retries:\n" + "\n".join(found)


def test_appearance_awaited_with_findby_not_waitfor_getby(lint):
    found = findings_for(lint, "waitfor-getby")
    assert not found, "waitFor wrapping a getBy* presence check; use await findBy*:\n" + "\n".join(found)


def test_findby_not_wrapped_in_truthy_assertion(lint):
    found = findings_for(lint, "findby-wrapped-in-truthy")
    assert not found, "expect(await findBy*()).toBeTruthy() is redundant:\n" + "\n".join(found)

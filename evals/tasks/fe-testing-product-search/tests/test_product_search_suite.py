import pytest
from conftest import findings_for, run_vitest, workspace

SEARCH = "src/products/ProductSearch.tsx"
MUTANTS = {
    "search_not_debounced": {SEARCH: [("useDebouncedValue(input.trim(), SEARCH_DELAY_MS)", "input.trim()")]},
    "search_term_not_sent": {"src/products/useProducts.ts": [("?q=${encodeURIComponent(searchTerm)}", "")]},
    "single_character_searched": {SEARCH: [("MIN_SEARCH_LENGTH = 2", "MIN_SEARCH_LENGTH = 1")]},
}


def test_suite_passes_against_real_search():
    result = run_vitest(workspace())
    assert result["total"] > 0, "no tests ran"
    assert result["failed"] == 0, "\n".join(result["failures"])[:4000]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(mutant):
    result = run_vitest(workspace(MUTANTS[mutant]))
    assert result["failed"] > 0, f"suite still passes with mutant {mutant}"


def test_fake_timers_not_enabled_before_async_queries(lint):
    found = findings_for(lint, "fake-timers-before-async-queries")
    assert not found, "fake timers switched on in a setup hook of a file that awaits findBy*/waitFor:\n" + "\n".join(found)


def test_fake_timers_restored_in_after_each(lint):
    if not lint["facts"].get("fakeTimersUsed"):
        pytest.skip("suite uses real timers only")
    assert lint["facts"].get("realTimersRestoredInAfterEach"), "vi.useFakeTimers() without vi.useRealTimers() in afterEach"


def test_http_is_mocked_with_msw(lint):
    assert lint["facts"].get("mswImported"), f"no msw handlers in the new test code: {lint['files']}"


def test_fetch_is_not_stubbed(lint):
    found = findings_for(lint, "fetch-mocked")
    assert not found, "stubs fetch instead of serving responses through MSW:\n" + "\n".join(found)


def test_product_data_hook_is_not_mocked(lint):
    found = [f for f in findings_for(lint, "data-module-mocked") if "useProducts" in f or "api/client" in f or "react-query" in f]
    assert not found, "mocks the data-fetching layer instead of running the real hook against MSW:\n" + "\n".join(found)

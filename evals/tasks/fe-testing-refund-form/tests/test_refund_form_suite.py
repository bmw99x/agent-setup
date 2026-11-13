import shutil

import pytest
from conftest import findings_for, run_vitest, workspace

FORM = "src/refunds/RefundRequestForm.tsx"
MUTANTS = {
    "blank_note_sent": {FORM: [("...(trimmedNote ? { note: trimmedNote } : {}),", "note: trimmedNote,")]},
    "amount_sent_in_pounds": {FORM: [("amountPence: Math.round(Number(amount) * 100),", "amountPence: Number(amount),")]},
    "refusal_not_shown": {FORM: [("{refundFailed && (", "{false && (")]},
}


def test_suite_passes_against_real_form():
    result = run_vitest(workspace())
    assert result["total"] > 0, "no tests ran"
    assert result["failed"] == 0, "\n".join(result["failures"])[:4000]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(mutant):
    result = run_vitest(workspace(MUTANTS[mutant]))
    assert result["failed"] > 0, f"suite still passes with mutant {mutant}"


def test_mantine_browser_stubs_live_in_the_setup_file():
    work = workspace()
    probe = work / "src" / "__verifier__"
    probe.mkdir(parents=True, exist_ok=True)
    shutil.copy("/tests/global_stubs.test.tsx", probe / "global_stubs.test.tsx")
    result = run_vitest(work, "src/__verifier__")
    assert result["total"] == 1 and result["failed"] == 0, (
        "a fresh test file can't render Mantine: the browser stubs aren't in the global setup file\n"
        + "\n".join(result["failures"])[:3000]
    )


def test_test_files_do_not_repeat_global_stubs(lint):
    found = findings_for(lint, "global-stub-in-test-file")
    assert not found, "matchMedia/ResizeObserver stubbed inside a test file instead of setupTests:\n" + "\n".join(found)


def test_request_body_expectation_has_no_undefined_keys(lint):
    found = findings_for(lint, "undefined-in-toEqual")
    assert not found, "toEqual with an undefined key passes whether or not the key is sent:\n" + "\n".join(found)


def test_http_is_mocked_with_msw(lint):
    assert lint["facts"].get("mswImported"), f"no msw handlers in the new test code: {lint['files']}"


def test_fetch_is_not_stubbed(lint):
    found = findings_for(lint, "fetch-mocked")
    assert not found, "stubs fetch instead of serving responses through MSW:\n" + "\n".join(found)


def test_refund_hook_is_not_mocked(lint):
    found = findings_for(lint, "data-module-mocked")
    assert not found, "mocks the data layer instead of running the real hook against MSW:\n" + "\n".join(found)

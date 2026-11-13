import sys

import pytest

sys.path.insert(0, "/tests")
from mantine_rules import (  # noqa: E402
    assert_no_braced_string_literals,
    assert_no_fractional_values,
    assert_no_hand_rolled_flex,
    assert_no_hardcoded_colors,
    assert_no_inline_style,
    assert_no_prop_only_css_class,
    check_vitest,
    findings,
    lint_tsx,
    run_project_checks,
    run_vitest_verifier,
)


@pytest.fixture(scope="session")
def results():
    return run_vitest_verifier("/tests/verifier.test.tsx")


@pytest.fixture(scope="session")
def report():
    return lint_tsx()


def test_invalid_email_blocks_sending(results):
    check_vitest(results, "invalid email is flagged on the field and nothing is sent")


def test_valid_invite_is_sent_and_confirmed(results):
    check_vitest(results, "valid invite is sent as a member, the dialog closes and the admin is told")


def test_form_state_lives_in_mantine_form(report):
    assert any(per_file["mantineFormImport"] for per_file in report.values()), "no @mantine/form import"
    hits = findings(report, "stateBoundInput")
    assert not hits, f"inputs bound to useState instead of @mantine/form: {hits}"


def test_no_alert(report):
    hits = findings(report, "alertCall")
    assert not hits, f"alert() used instead of a Mantine notification: {hits}"


def test_no_inline_style_objects(report):
    assert_no_inline_style(report)


def test_no_css_class_that_props_could_express():
    assert_no_prop_only_css_class()


def test_no_hand_rolled_flex_layout(report):
    assert_no_hand_rolled_flex(report)


def test_no_braced_string_literal_props(report):
    assert_no_braced_string_literals(report)


def test_no_fractional_values(report):
    assert_no_fractional_values(report)


def test_theme_colors_not_hardcoded(report):
    assert_no_hardcoded_colors(report)


def test_project_tests_and_typecheck_pass():
    run_project_checks()

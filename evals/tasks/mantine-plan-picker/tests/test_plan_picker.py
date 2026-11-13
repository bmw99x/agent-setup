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


def test_each_plan_is_a_radio_with_the_selected_plan_checked(results):
    check_vitest(results, "each plan is a radio and the selected plan is checked")


def test_clicking_anywhere_on_a_card_selects_it(results):
    check_vitest(results, "clicking anywhere on a card selects that plan")


def test_billing_page_tracks_the_selected_plan(results):
    check_vitest(results, "billing page starts on the account plan and tracks the selection")


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


def test_no_createStyles(report):
    hits = findings(report, "createStyles")
    assert not hits, f"createStyles / @mantine/emotion is gone in current Mantine: {hits}"


def test_project_tests_and_typecheck_pass():
    run_project_checks()

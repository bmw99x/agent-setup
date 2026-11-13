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


def test_order_summary_still_renders_lines_and_total(results):
    check_vitest(results, "order summary shows every line, the total and the VAT note")


def test_bordered_panel_is_a_paper_or_card(results):
    check_vitest(results, "panel surface is a Mantine Paper or Card")


def test_theme_colors_not_hardcoded(report):
    assert_no_hardcoded_colors(report)


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


def test_project_tests_and_typecheck_pass():
    run_project_checks()

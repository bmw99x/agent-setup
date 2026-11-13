import pytest
from conftest import collected, docstring_problem, run_pytest, separator_lines, agent_test_functions, workspace

TOTALS = "app/pricing/totals.py"
MUTANTS = {
    "discount_code_ignored": [("(subtotal * (1 - rate))", "(subtotal * 1)")],
    "unknown_code_accepted": [("raise UnknownDiscountCodeError(code)",
                               "return subtotal.quantize(CENT, rounding=ROUND_HALF_UP)")],
    "shipping_never_free": [('return Decimal("0.00")', "return SHIPPING_FEE")],
}


def test_suite_passes_on_real_code(agent_files):
    proc = run_pytest(workspace())
    assert proc.returncode == 0, proc.stdout[-3000:]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(agent_files, mutant):
    proc = run_pytest(workspace({TOTALS: MUTANTS[mutant]}))
    assert proc.returncode == 1, f"suite still passes with mutant {mutant}:\n{proc.stdout[-2000:]}"


def test_pure_logic_tests_marked_unit(agent_files):
    work = workspace()
    total = collected(work)
    assert total > 0
    assert collected(work, "-m", "unit") == total, "every test of pure pricing logic should carry the unit marker"
    assert collected(work, "-m", "integration") == 0


def test_docstrings_are_given_when_then_blocks(agent_files):
    problems = [f"{p.name}::{n.name}: {why}" for p, n in agent_test_functions(agent_files)
                if (why := docstring_problem(n))]
    assert not problems, "\n".join(problems)


def test_no_separator_banner_comments(agent_files):
    assert not separator_lines(agent_files)

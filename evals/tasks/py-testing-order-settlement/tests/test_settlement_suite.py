import ast

import pytest
from conftest import agent_test_functions, collected, docstring_problem, run_pytest, workspace

SETTLEMENT = "app/orders/settlement.py"
MUTANTS = {
    "success_not_notified": [("await notifier.payment_succeeded(order)", "pass")],
    "decline_reraised": [("await notifier.payment_failed(order, str(declined))\n        return order",
                          "await notifier.payment_failed(order, str(declined))\n        raise")],
    "paid_order_charged_again": [("if order.status is OrderStatus.PAID:", "if False:")],
}


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return ""


def test_suite_passes_on_real_code(agent_files):
    proc = run_pytest(workspace())
    assert proc.returncode == 0, proc.stdout[-3000:]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(agent_files, mutant):
    proc = run_pytest(workspace({SETTLEMENT: MUTANTS[mutant]}))
    assert proc.returncode == 1, f"suite still passes with mutant {mutant}:\n{proc.stdout[-2000:]}"


def test_collaborators_injected_not_patched(agent_files):
    """Fakes go in through settle_order's parameters; nothing patches module globals."""
    offenders = []
    for path in agent_files:
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            name = _dotted(node.func)
            parts = name.split(".")
            if "patch" in parts or name.endswith(("monkeypatch.setattr", "monkeypatch.delattr")):
                offenders.append(f"{path.name}:{node.lineno}: {name}(...)")
    assert not offenders, "\n".join(offenders)


def test_fake_driven_tests_marked_unit(agent_files):
    work = workspace()
    total = collected(work)
    assert total > 0
    assert collected(work, "-m", "unit") == total, "tests driven by injected fakes should carry the unit marker"
    assert collected(work, "-m", "integration") == 0


def test_docstrings_are_given_when_then_blocks(agent_files):
    problems = [f"{p.name}::{n.name}: {why}" for p, n in agent_test_functions(agent_files)
                if (why := docstring_problem(n))]
    assert not problems, "\n".join(problems)

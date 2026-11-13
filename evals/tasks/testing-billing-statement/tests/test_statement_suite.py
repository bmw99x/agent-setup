import filecmp

import pytest
from conftest import APP, BASE, run_pytest, workspace

STATEMENTS = "app/billing/statements.py"
MUTANTS = {
    "first_page_only": [("        if not cursor:\n            return", "        return")],
    "voided_invoices_billed": [("if not invoice.get(\"voided_at\")]", "if True]")],
    "credit_notes_ignored": [("sum(note[\"amount\"] for note in invoice.get(\"credit_notes\", []))", "0")],
}


def _tree_diff(left, right, prefix=""):
    cmp = filecmp.dircmp(left, right, ignore=["__pycache__"])
    out = [f"{prefix}{n}" for n in cmp.left_only + cmp.right_only + cmp.diff_files]
    for name, sub in cmp.subdirs.items():
        out += _tree_diff(sub.left, sub.right, f"{prefix}{name}/")
    return out


def test_suite_passes_on_real_code(agent_files):
    proc = run_pytest(workspace())
    assert proc.returncode == 0, proc.stdout[-3000:]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(agent_files, mutant):
    """Fake responses mirror the provider's full payload, so behaviour driven by any part of it is pinned."""
    proc = run_pytest(workspace({STATEMENTS: MUTANTS[mutant]}))
    assert proc.returncode == 1, f"suite still passes with mutant {mutant}:\n{proc.stdout[-2000:]}"


def test_production_code_unchanged():
    changed = [f"app/{p}" for p in _tree_diff(BASE / "app", APP / "app")]
    assert not changed, "production files changed: " + ", ".join(changed)

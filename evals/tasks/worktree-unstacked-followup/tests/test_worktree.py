import importlib
import sys

import pytest

from gitstate import (
    assert_based_on_main,
    assert_branch_convention,
    assert_in_linked_worktree,
    assert_not_nested,
    assert_original_checkout_untouched,
    assert_pushed,
    assert_worktree_dir_short_kebab,
    changed_paths,
    cleanup,
    export_branch,
    run_pytest,
    task_branch,
)

UNMERGED = "feat/order-discounts"
UNMERGED_PATHS = {"billing/discounts.py", "tests/test_discounts.py"}


def test_invoice_numbering_committed_and_pushed():
    branch = task_branch()
    assert_pushed(branch)
    assert "billing/invoices.py" in changed_paths(branch)
    assert any(p.startswith("tests/") for p in changed_paths(branch)), "no tests committed"
    tree = export_branch(branch)
    try:
        sys.path.insert(0, str(tree))
        invoices = importlib.import_module("billing.invoices")
        assert invoices.invoice_number(2026, 42) == "INV-2026-00042"
        assert invoices.invoice_number(2027, 99999) == "INV-2027-99999"
        for bad in (0, 100000):
            with pytest.raises(ValueError):
                invoices.invoice_number(2026, bad)
        out = run_pytest(tree)
        assert out.returncode == 0, out.stdout
    finally:
        sys.path.remove(str(tree))
        for name in [m for m in sys.modules if m == "billing" or m.startswith("billing.")]:
            del sys.modules[name]
        cleanup(tree)


def test_feature_work_happens_in_its_own_worktree():
    assert_in_linked_worktree(task_branch())


def test_original_checkout_not_switched():
    assert_original_checkout_untouched()


def test_pushed_branch_cut_from_default_branch_not_unmerged_mr():
    branch = task_branch()
    assert_pushed(branch)
    assert_based_on_main(branch, UNMERGED)


def test_pushed_diff_independent_of_unmerged_mr():
    leaked = changed_paths(task_branch()) & UNMERGED_PATHS
    assert not leaked, f"MR diff would include the unmerged discounts work: {leaked}"


def test_worktree_not_nested():
    assert_not_nested(task_branch())


def test_branch_follows_project_convention():
    assert_branch_convention(task_branch(), "feat/")


def test_worktree_path_short_kebab_case():
    assert_worktree_dir_short_kebab(task_branch())

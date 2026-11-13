import importlib
import sys

from gitstate import (
    assert_based_on_main,
    assert_branch_convention,
    assert_dirty_work_untouched,
    assert_in_linked_worktree,
    assert_not_nested,
    assert_original_checkout_untouched,
    assert_worktree_dir_short_kebab,
    changed_paths,
    cleanup,
    export_branch,
    git,
    run_pytest,
    task_branch,
)

UNMERGED = "feat/csv-export"


def test_low_stock_feature_committed():
    branch = task_branch()
    assert "stock/alerts.py" in changed_paths(branch)
    assert any(p.startswith("tests/") for p in changed_paths(branch)), "no tests committed"
    tree = export_branch(branch)
    try:
        sys.path.insert(0, str(tree))
        from stock.items import Item
        alerts = importlib.import_module("stock.alerts")
        items = [Item("A", "a", 7), Item("B", "b", 2), Item("C", "c", 0), Item("D", "d", 5)]
        assert [i.sku for i in alerts.low_stock(items)] == ["C", "B"]
        assert [i.sku for i in alerts.low_stock(items, threshold=8)] == ["C", "B", "D", "A"]
        out = run_pytest(tree)
        assert out.returncode == 0, out.stdout
    finally:
        sys.path.remove(str(tree))
        for name in [m for m in sys.modules if m == "stock" or m.startswith("stock.")]:
            del sys.modules[name]
        cleanup(tree)


def test_feature_work_happens_in_its_own_worktree():
    assert_in_linked_worktree(task_branch())


def test_original_checkout_not_switched():
    assert_original_checkout_untouched()


def test_uncommitted_work_left_in_place():
    assert_dirty_work_untouched()


def test_branch_cut_from_default_branch_not_unmerged_feature():
    assert_based_on_main(task_branch(), UNMERGED)


def test_wip_not_carried_into_new_branch():
    branch = task_branch()
    leaked = changed_paths(branch) & {"tests/test_csv_export.py", "EXPORT-NOTES.md"}
    assert not leaked, leaked
    assert "format_report_as" not in git("show", f"{branch}:stock/report.py"), "WIP report edit committed"


def test_worktree_not_nested():
    assert_not_nested(task_branch())


def test_branch_follows_project_convention():
    assert_branch_convention(task_branch(), "feat/")


def test_worktree_path_short_kebab_case():
    assert_worktree_dir_short_kebab(task_branch())

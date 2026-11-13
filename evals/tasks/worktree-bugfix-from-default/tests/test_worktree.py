import importlib
import sys
from decimal import Decimal

from gitstate import (
    BASE,
    REPO,
    assert_based_on_main,
    assert_branch_convention,
    assert_dirty_work_untouched,
    assert_in_linked_worktree,
    assert_not_nested,
    assert_original_checkout_untouched,
    assert_pushed,
    assert_worktree_dir_short_kebab,
    changed_paths,
    cleanup,
    digest,
    export_branch,
    git,
    run_pytest,
    task_branch,
)

UNMERGED = "feat/label-printing"
ENV_CONTENT = "SHIPPING_ORIGIN_POSTCODE=LS1 4AP\nSHIPPING_LABEL_API_KEY=sk_live_local_only_7f3a\n"


def test_fix_committed_and_pushed():
    branch = task_branch()
    assert_pushed(branch)
    assert "shipping/rates.py" in changed_paths(branch)
    assert any(p.startswith("tests/") for p in changed_paths(branch)), "no regression test committed"
    tree = export_branch(branch)
    try:
        sys.path.insert(0, str(tree))
        rates = importlib.import_module("shipping.rates")
        assert rates.parcel_price(Decimal("2")) == Decimal("4.50")
        assert rates.parcel_price(Decimal("1.99")) == Decimal("4.50")
        assert rates.parcel_price(Decimal("2.01")) == Decimal("7.90")
        (tree / ".env").write_text(ENV_CONTENT)
        out = run_pytest(tree)
        assert out.returncode == 0, out.stdout
    finally:
        sys.path.remove(str(tree))
        for name in [m for m in sys.modules if m == "shipping" or m.startswith("shipping.")]:
            del sys.modules[name]
        cleanup(tree)


def test_bugfix_happens_in_its_own_worktree():
    assert_in_linked_worktree(task_branch())


def test_original_checkout_not_switched():
    assert_original_checkout_untouched()


def test_uncommitted_work_left_in_place():
    assert_dirty_work_untouched()
    env = REPO / ".env"
    assert not env.is_symlink() and digest(env) == BASE["env_file"], "original .env changed"


def test_fix_branch_cut_from_default_branch_not_feature_branch():
    branch = task_branch()
    assert_pushed(branch)
    assert_based_on_main(branch, UNMERGED)


def test_wip_not_carried_into_fix():
    branch = task_branch()
    assert "tests/test_labels.py" not in changed_paths(branch), "WIP label test committed"
    assert "label_with_price" not in git("log", "-p", f"{BASE['main']}..{branch}"), "WIP label edit committed"


def test_env_file_copied_into_worktree_not_symlinked():
    worktree = assert_in_linked_worktree(task_branch())
    if worktree is None:
        return  # worktree already cleaned up; nothing left to inspect
    env = worktree / ".env"
    assert env.exists(), "worktree has no .env; the test suite cannot run there"
    assert not env.is_symlink(), "worktree .env is a symlink; copy it"
    assert digest(env) == BASE["env_file"], "worktree .env differs from the local one"


def test_env_file_not_committed():
    branch = task_branch()
    committed = git("log", "--format=", "--name-only", f"{BASE['main']}..{branch}").split()
    assert ".env" not in committed, ".env was committed"
    assert "sk_live_local_only_7f3a" not in git("log", "-p", f"{BASE['main']}..{branch}"), "secret committed"


def test_worktree_not_nested():
    assert_not_nested(task_branch())


def test_branch_follows_project_convention():
    assert_branch_convention(task_branch(), "fix/")


def test_worktree_path_short_kebab_case():
    assert_worktree_dir_short_kebab(task_branch())

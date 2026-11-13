import sys

sys.path.insert(0, "/tests")

from plan_lib import (  # noqa: E402
    BASE,
    by_number,
    depended_upon,
    describe,
    is_entry_point,
    is_production,
    is_schema_change,
    is_test,
    leaves,
    slices,
)

BEHAVIOURS = 4  # request, cancel, approve, list pending


def test_plan_uses_requested_format():
    assert slices(), "SLICES.md has no '## Slice N:' sections"
    numbers = [slice_.number for slice_ in slices()]
    assert len(numbers) == len(set(numbers)), f"duplicate slice numbers: {numbers}"
    for slice_ in slices():
        assert slice_.files, f"no Files: list parsed for {describe(slice_)}"
        unknown = slice_.depends_on - set(by_number())
        assert not unknown, f"{describe(slice_)} depends on slices that do not exist: {unknown}"


def test_plan_paths_fit_the_repo():
    paths = {path for slice_ in slices() for path in slice_.files}
    misplaced = [path for path in paths if not (BASE / path).parent.exists() and not (BASE / path).parent.parent.exists()]
    assert not misplaced, f"paths that do not fit the repo layout: {misplaced}"


def test_shared_schema_goes_in_a_foundation_slice_first():
    first = slices()[0]
    assert any(is_schema_change(path) for path in first.files), f"first slice adds no schema/migration: {describe(first)}"
    assert not first.depends_on, f"first slice has dependencies: {describe(first)}"
    waiting = [slice_ for slice_ in leaves() if first.number not in slice_.depends_on]
    assert not waiting, "behaviour slices that do not build on the foundation: " + "; ".join(map(describe, waiting))


def test_schema_changed_in_one_slice_only():
    touching = [slice_ for slice_ in slices() if any(is_schema_change(path) for path in slice_.files)]
    assert len(touching) == 1, "models/migrations edited by several slices: " + "; ".join(map(describe, touching))


def test_no_stacked_dependency_chain():
    stacked = [slice_ for slice_ in depended_upon() if slice_.depends_on]
    assert not stacked, "slices that others wait on but which themselves wait on another: " + "; ".join(map(describe, stacked))


def test_one_behaviour_per_slice():
    assert len(leaves()) >= BEHAVIOURS, (
        f"{BEHAVIOURS} user-visible behaviours but only {len(leaves())} independent behaviour slices: "
        + "; ".join(map(describe, leaves()))
    )


def test_behaviour_slices_are_vertical():
    flat = []
    for slice_ in leaves():
        entry = [path for path in slice_.files if is_entry_point(path)]
        logic = [path for path in slice_.files if is_production(path) and not is_entry_point(path)]
        tests = [path for path in slice_.files if is_test(path)]
        if not (entry and logic and tests):
            flat.append(slice_)
    assert not flat, "behaviour slices missing an entry point, the logic behind it, or a test: " + "; ".join(map(describe, flat))

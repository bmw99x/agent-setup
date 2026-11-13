import sys

sys.path.insert(0, "/tests")

from plan_lib import (  # noqa: E402
    BASE,
    by_number,
    describe,
    is_entry_point,
    is_production,
    is_schema_change,
    is_test,
    slices,
)

BEHAVIOURS = 3


def reaches_beyond_persistence(slice_) -> bool:
    return any(is_production(path) and not is_schema_change(path) for path in slice_.files)


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


def test_schema_change_ships_with_the_behaviour_that_needs_it():
    migrating = [slice_ for slice_ in slices() if any(is_schema_change(path) for path in slice_.files)]
    assert migrating, "no slice adds the delivery-instructions column (no models.py or migration listed)"
    split_off = [
        slice_
        for slice_ in migrating
        if not (reaches_beyond_persistence(slice_) and any(is_test(path) for path in slice_.files))
    ]
    assert not split_off, "schema change split from the behaviour that uses it: " + "; ".join(map(describe, split_off))


def test_behaviour_slices_do_not_depend_on_each_other():
    waiting = [slice_ for slice_ in slices() if slice_.depends_on]
    assert not waiting, "independent backlog items chained together: " + "; ".join(map(describe, waiting))


def test_one_behaviour_per_slice():
    with_entry_or_contract = [slice_ for slice_ in slices() if reaches_beyond_persistence(slice_)]
    assert len(with_entry_or_contract) >= BEHAVIOURS, (
        f"{BEHAVIOURS} backlog items but only {len(with_entry_or_contract)} behaviour slices: "
        + "; ".join(map(describe, slices()))
    )


def test_every_slice_is_vertical():
    flat = [
        slice_
        for slice_ in slices()
        if not (reaches_beyond_persistence(slice_) and any(is_test(path) for path in slice_.files))
    ]
    assert not flat, "slices that ship a layer, not a tested behaviour: " + "; ".join(map(describe, flat))


def test_new_endpoints_ship_with_their_entry_point():
    routed = [slice_ for slice_ in slices() if any(is_entry_point(path) for path in slice_.files)]
    assert len(routed) >= 2, (
        "overdue-deliveries and CSV export each need an entry point in their own slice: "
        + "; ".join(map(describe, slices()))
    )

import re
import sys

sys.path.insert(0, "/tests")

from plan_lib import (  # noqa: E402
    BASE,
    by_number,
    depended_upon,
    describe,
    is_production,
    is_schema_change,
    is_test,
    leaves,
    slices,
)

SMS = re.compile(r"sms|text_?message", re.I)
PUSH = re.compile(r"push", re.I)


def channel_files(slice_, channel: re.Pattern) -> list[str]:
    return [path for path in slice_.files if is_production(path) and channel.search(path)]


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


def test_shared_core_is_a_foundation_slice_first():
    first = slices()[0]
    assert not first.depends_on, f"first slice has dependencies: {describe(first)}"
    builders = [slice_ for slice_ in slices() if first.number in slice_.depends_on]
    assert len(builders) >= 2, f"first slice is not a foundation that 2+ slices build on: {describe(first)}"


def test_foundation_carries_no_channel_behaviour():
    piggybacked = [
        slice_ for slice_ in depended_upon() if channel_files(slice_, SMS) or channel_files(slice_, PUSH)
    ]
    assert not piggybacked, "SMS/push delivery inside a slice others wait on: " + "; ".join(map(describe, piggybacked))


def test_sms_and_push_are_separate_slices():
    sms = [slice_ for slice_ in slices() if channel_files(slice_, SMS)]
    push = [slice_ for slice_ in slices() if channel_files(slice_, PUSH)]
    assert sms and push, "plan has no SMS or no push slice touching production code"
    both = [slice_ for slice_ in sms if slice_ in push]
    assert not both, "SMS and push delivered in the same slice: " + "; ".join(map(describe, both))


def test_no_stacked_dependency_chain():
    stacked = [slice_ for slice_ in depended_upon() if slice_.depends_on]
    assert not stacked, "slices that others wait on but which themselves wait on another: " + "; ".join(map(describe, stacked))


def test_behaviour_slices_are_vertical():
    flat = [
        slice_
        for slice_ in leaves()
        if not (
            any(is_test(path) for path in slice_.files)
            and any(is_production(path) and not is_schema_change(path) for path in slice_.files)
        )
    ]
    assert not flat, "behaviour slices without a test or without behaviour code: " + "; ".join(map(describe, flat))

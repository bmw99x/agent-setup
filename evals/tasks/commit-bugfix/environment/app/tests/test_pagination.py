import sys

sys.path.insert(0, "src")
from pagination import paginate  # noqa: E402


def test_first_page():
    assert paginate(list(range(10)), 1, 3) == [0, 1, 2]


def test_last_page():
    assert paginate(list(range(10)), 4, 3) == [9]

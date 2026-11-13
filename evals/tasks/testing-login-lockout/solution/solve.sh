#!/bin/bash
mkdir -p /app/tests
cat > /app/tests/conftest.py <<'PY'
import pytest

from app.auth import login
from app.auth.throttle import LoginThrottle


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeDirectory:
    def __init__(self, passwords: dict[str, str]) -> None:
        self.passwords = passwords
        self.checked: list[str] = []

    def verify(self, username: str, password: str) -> bool:
        self.checked.append(username)
        return self.passwords.get(username.casefold()) == password


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture(autouse=True)
def fresh_throttle(monkeypatch, clock):
    throttle = LoginThrottle(clock=clock)
    monkeypatch.setattr(login, "throttle", throttle)
    return throttle


@pytest.fixture
def directory() -> FakeDirectory:
    return FakeDirectory({"alice": "s3cret"})
PY
cat > /app/tests/test_login_lockout.py <<'PY'
import pytest

from app.auth.login import AccountLockedError, InvalidCredentialsError, authenticate


def fail(times: int, directory, username: str = "alice") -> None:
    for _ in range(times):
        with pytest.raises(InvalidCredentialsError):
            authenticate(username, "wrong", directory=directory)


def test_four_failures_do_not_lock(directory):
    fail(4, directory)
    assert authenticate("alice", "s3cret", directory=directory) == "alice"


def test_fifth_failure_locks_even_correct_password(directory):
    fail(5, directory)
    directory.checked.clear()
    with pytest.raises(AccountLockedError):
        authenticate("alice", "s3cret", directory=directory)
    assert directory.checked == []


def test_lock_lifts_after_window(directory, clock):
    fail(5, directory)
    clock.advance(15 * 60 + 1)
    assert authenticate("alice", "s3cret", directory=directory) == "alice"


def test_lock_holds_inside_window(directory, clock):
    fail(5, directory)
    clock.advance(15 * 60 - 1)
    with pytest.raises(AccountLockedError):
        authenticate("alice", "s3cret", directory=directory)


def test_success_clears_failures(directory):
    fail(4, directory)
    authenticate("alice", "s3cret", directory=directory)
    fail(4, directory)
    assert authenticate("alice", "s3cret", directory=directory) == "alice"


def test_username_case_insensitive(directory):
    fail(3, directory, "alice")
    fail(2, directory, "ALICE")
    with pytest.raises(AccountLockedError):
        authenticate("Alice", "s3cret", directory=directory)
PY

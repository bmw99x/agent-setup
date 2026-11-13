"""Failed-login throttling: lock an account after repeated failures inside a sliding window."""

import time
from collections import defaultdict, deque
from collections.abc import Callable

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class LoginThrottle:
    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
    ) -> None:
        self._clock = clock
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._failures: defaultdict[str, deque[float]] = defaultdict(deque)

    def is_locked(self, username: str) -> bool:
        return len(self._recent_failures(username)) >= self._max_failures

    def record_failure(self, username: str) -> None:
        self._failures[username.casefold()].append(self._clock())

    def record_success(self, username: str) -> None:
        self._failures.pop(username.casefold(), None)

    def _recent_failures(self, username: str) -> deque[float]:
        failures = self._failures[username.casefold()]
        cutoff = self._clock() - self._window_seconds
        while failures and failures[0] <= cutoff:
            failures.popleft()
        return failures


throttle = LoginThrottle()

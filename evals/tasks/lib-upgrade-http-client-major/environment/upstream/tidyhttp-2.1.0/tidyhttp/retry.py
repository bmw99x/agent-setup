import time
from collections.abc import Callable
from typing import TypeVar

from tidyhttp.errors import HTTPError

T = TypeVar("T")


class Backoff:
    def __init__(self, *, base: float = 0.5, factor: float = 2.0) -> None:
        self.base = base
        self.factor = factor

    def delay(self, attempt: int) -> float:
        return self.base * self.factor ** (attempt - 1)


class RetryPolicy:
    def __init__(self, max_attempts: int = 3, retry_on: tuple[int, ...] = (502, 503, 504), backoff: Backoff | None = None) -> None:
        self.max_attempts = max_attempts
        self.retry_on = retry_on
        self.backoff = backoff or Backoff()

    def run(self, call: Callable[[], T]) -> T:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return call()
            except HTTPError as error:
                if error.status not in self.retry_on or attempt == self.max_attempts:
                    raise
                time.sleep(self.backoff.delay(attempt))
        raise AssertionError("unreachable")

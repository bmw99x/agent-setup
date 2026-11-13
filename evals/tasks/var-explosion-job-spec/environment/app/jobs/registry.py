from dataclasses import dataclass, field
from itertools import count


@dataclass
class Job:
    id: int
    name: str
    command: str
    cron: str | None
    interval_seconds: int | None
    retries: int
    timeout_seconds: int
    env: dict[str, str]
    queue: str
    argv: list[str] = field(default_factory=list)


JOBS: dict[int, Job] = {}
_ids = count(1)


def next_job_id() -> int:
    return next(_ids)


def clear() -> None:
    JOBS.clear()

#!/bin/bash
set -euo pipefail
cat > /app/jobs/spec.py <<'PY'
import shlex
from dataclasses import dataclass, field

DEFAULT_TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class JobSpec:
    command: str
    cron: str | None = None
    interval_seconds: int | None = None
    retries: int = 3
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    env: dict[str, str] = field(default_factory=dict)
    queue: str = "default"

    def __post_init__(self) -> None:
        if (self.cron is None) == (self.interval_seconds is None):
            raise ValueError("give exactly one of cron or interval_seconds")
        if self.retries < 0:
            raise ValueError("retries must not be negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


def build_worker_argv(spec: JobSpec) -> list[str]:
    argv = ["worker", "--queue", spec.queue]
    if spec.retries:
        argv.extend(["--retries", str(spec.retries)])
    if spec.timeout_seconds != DEFAULT_TIMEOUT_SECONDS:
        argv.extend(["--timeout", str(spec.timeout_seconds)])
    for key in sorted(spec.env):
        argv.append(f"--env={key}={spec.env[key]}")
    argv.extend(["--", *shlex.split(spec.command)])
    return argv
PY
cat > /app/jobs/registry.py <<'PY'
from dataclasses import dataclass
from itertools import count

from jobs.spec import JobSpec


@dataclass
class Job:
    id: int
    name: str
    spec: JobSpec
    argv: list[str]


JOBS: dict[int, Job] = {}
_ids = count(1)


def next_job_id() -> int:
    return next(_ids)


def clear() -> None:
    JOBS.clear()
PY
cat > /app/jobs/scheduler.py <<'PY'
import shlex
from typing import Any

from jobs.registry import JOBS, Job, next_job_id
from jobs.spec import JobSpec, build_worker_argv


def schedule_job(name: str, spec: JobSpec | None = None, **legacy_settings: Any) -> Job:
    # Transition aid for billing_plugin, which still passes loose settings; remove once it migrates.
    spec = spec or JobSpec(**legacy_settings)
    job = Job(next_job_id(), name, spec, build_worker_argv(spec))
    JOBS[job.id] = job
    return job


def reschedule_job(job_id: int, spec: JobSpec) -> Job:
    job = Job(job_id, JOBS[job_id].name, spec, build_worker_argv(spec))
    JOBS[job_id] = job
    return job


def preview_job(spec: JobSpec) -> str:
    trigger = f"cron {spec.cron}" if spec.cron is not None else f"every {spec.interval_seconds}s"
    return f"[{trigger}] {shlex.join(build_worker_argv(spec))}"
PY
cat > /app/jobs/nightly.py <<'PY'
from jobs.registry import Job
from jobs.scheduler import preview_job, schedule_job
from jobs.spec import JobSpec

SEARCH_REINDEX = JobSpec(command="search reindex --full", cron="0 1 * * *", timeout_seconds=3600, queue="heavy")


def register_nightly_jobs() -> list[Job]:
    return [
        schedule_job("search-reindex", SEARCH_REINDEX),
        schedule_job("cache-warm", JobSpec(command="cache warm", interval_seconds=900, retries=0)),
        schedule_job(
            "export-orders",
            JobSpec(
                command="orders export --since yesterday",
                cron="30 2 * * *",
                env={"EXPORT_BUCKET": "orders-exports", "AWS_REGION": "eu-west-2"},
            ),
        ),
    ]


def describe_nightly_reindex() -> str:
    return preview_job(SEARCH_REINDEX)
PY
cat > /app/jobs/admin.py <<'PY'
from dataclasses import replace

from jobs.registry import JOBS, Job
from jobs.scheduler import reschedule_job


def move_to_queue(job_id: int, queue: str) -> Job:
    return reschedule_job(job_id, replace(JOBS[job_id].spec, queue=queue))


def pause_retries(job_id: int) -> Job:
    return reschedule_job(job_id, replace(JOBS[job_id].spec, retries=0))
PY

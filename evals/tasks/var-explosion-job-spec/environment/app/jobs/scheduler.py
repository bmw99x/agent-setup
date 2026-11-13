import shlex

from jobs.registry import JOBS, Job, next_job_id

DEFAULT_TIMEOUT_SECONDS = 300


def schedule_job(
    name: str,
    command: str,
    cron: str | None = None,
    interval_seconds: int | None = None,
    retries: int = 3,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    env: dict[str, str] | None = None,
    queue: str = "default",
) -> Job:
    if (cron is None) == (interval_seconds is None):
        raise ValueError("give exactly one of cron or interval_seconds")
    if retries < 0:
        raise ValueError("retries must not be negative")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    argv = ["worker", "--queue", queue]
    if retries:
        argv.extend(["--retries", str(retries)])
    if timeout_seconds != DEFAULT_TIMEOUT_SECONDS:
        argv.extend(["--timeout", str(timeout_seconds)])
    if env:
        for key in sorted(env):
            argv.append(f"--env={key}={env[key]}")
    argv.extend(["--", *shlex.split(command)])
    job = Job(next_job_id(), name, command, cron, interval_seconds, retries, timeout_seconds, dict(env or {}), queue, argv)
    JOBS[job.id] = job
    return job


def reschedule_job(
    job_id: int,
    command: str,
    cron: str | None = None,
    interval_seconds: int | None = None,
    retries: int = 3,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    env: dict[str, str] | None = None,
    queue: str = "default",
) -> Job:
    if (cron is None) == (interval_seconds is None):
        raise ValueError("give exactly one of cron or interval_seconds")
    if retries < 0:
        raise ValueError("retries must not be negative")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    argv = ["worker", "--queue", queue]
    if retries:
        argv.extend(["--retries", str(retries)])
    if timeout_seconds != DEFAULT_TIMEOUT_SECONDS:
        argv.extend(["--timeout", str(timeout_seconds)])
    if env:
        for key in sorted(env):
            argv.append(f"--env={key}={env[key]}")
    argv.extend(["--", *shlex.split(command)])
    old = JOBS[job_id]
    job = Job(job_id, old.name, command, cron, interval_seconds, retries, timeout_seconds, dict(env or {}), queue, argv)
    JOBS[job_id] = job
    return job


def preview_job(
    command: str,
    cron: str | None = None,
    interval_seconds: int | None = None,
    retries: int = 3,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    env: dict[str, str] | None = None,
    queue: str = "default",
) -> str:
    argv = ["worker", "--queue", queue]
    if retries:
        argv.extend(["--retries", str(retries)])
    if timeout_seconds != DEFAULT_TIMEOUT_SECONDS:
        argv.extend(["--timeout", str(timeout_seconds)])
    if env:
        for key in sorted(env):
            argv.append(f"--env={key}={env[key]}")
    argv.extend(["--", *shlex.split(command)])
    trigger = f"cron {cron}" if cron is not None else f"every {interval_seconds}s"
    return f"[{trigger}] {shlex.join(argv)}"

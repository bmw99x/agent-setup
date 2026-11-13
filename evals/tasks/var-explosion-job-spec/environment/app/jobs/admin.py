from jobs.registry import JOBS, Job
from jobs.scheduler import reschedule_job


def move_to_queue(job_id: int, queue: str) -> Job:
    job = JOBS[job_id]
    return reschedule_job(
        job_id,
        command=job.command,
        cron=job.cron,
        interval_seconds=job.interval_seconds,
        retries=job.retries,
        timeout_seconds=job.timeout_seconds,
        env=job.env,
        queue=queue,
    )


def pause_retries(job_id: int) -> Job:
    job = JOBS[job_id]
    return reschedule_job(
        job_id,
        command=job.command,
        cron=job.cron,
        interval_seconds=job.interval_seconds,
        retries=0,
        timeout_seconds=job.timeout_seconds,
        env=job.env,
        queue=job.queue,
    )

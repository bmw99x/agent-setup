from jobs.registry import Job
from jobs.scheduler import preview_job, schedule_job


def register_nightly_jobs() -> list[Job]:
    return [
        schedule_job(
            name="search-reindex",
            command="search reindex --full",
            cron="0 1 * * *",
            timeout_seconds=3600,
            queue="heavy",
        ),
        schedule_job(
            name="cache-warm",
            command="cache warm",
            interval_seconds=900,
            retries=0,
        ),
        schedule_job(
            name="export-orders",
            command="orders export --since yesterday",
            cron="30 2 * * *",
            env={"EXPORT_BUCKET": "orders-exports", "AWS_REGION": "eu-west-2"},
        ),
    ]


def describe_nightly_reindex() -> str:
    return preview_job(command="search reindex --full", cron="0 1 * * *", timeout_seconds=3600, queue="heavy")

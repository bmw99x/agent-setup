from jobs.scheduler import schedule_job


def install() -> list:
    return [
        schedule_job(
            name="invoice-run",
            command="billing invoice --all",
            cron="0 2 * * *",
            retries=5,
            env={"BILLING_MODE": "live"},
        ),
        schedule_job(name="dunning", command="billing dunning", interval_seconds=3600),
    ]

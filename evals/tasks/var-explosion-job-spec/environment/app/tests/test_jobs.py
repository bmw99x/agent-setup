import pytest

from billing_plugin.hooks import install
from jobs import registry
from jobs.admin import move_to_queue, pause_retries
from jobs.nightly import describe_nightly_reindex, register_nightly_jobs
from jobs.scheduler import schedule_job


@pytest.fixture(autouse=True)
def empty_registry():
    registry.clear()
    yield
    registry.clear()


def test_nightly_jobs_worker_argv():
    reindex, warm, export = register_nightly_jobs()
    assert reindex.argv == ["worker", "--queue", "heavy", "--retries", "3", "--timeout", "3600", "--", "search", "reindex", "--full"]
    assert warm.argv == ["worker", "--queue", "default", "--", "cache", "warm"]
    assert export.argv == [
        "worker", "--queue", "default", "--retries", "3",
        "--env=AWS_REGION=eu-west-2", "--env=EXPORT_BUCKET=orders-exports",
        "--", "orders", "export", "--since", "yesterday",
    ]
    assert [j.name for j in registry.JOBS.values()] == ["search-reindex", "cache-warm", "export-orders"]


def test_preview():
    assert describe_nightly_reindex() == (
        "[cron 0 1 * * *] worker --queue heavy --retries 3 --timeout 3600 -- search reindex --full"
    )


def test_move_to_queue_keeps_everything_else():
    reindex, *_ = register_nightly_jobs()
    moved = move_to_queue(reindex.id, "batch")
    assert moved.id == reindex.id and moved.name == "search-reindex"
    assert moved.argv == ["worker", "--queue", "batch", "--retries", "3", "--timeout", "3600", "--", "search", "reindex", "--full"]


def test_pause_retries():
    _, _, export = register_nightly_jobs()
    assert "--retries" not in pause_retries(export.id).argv


def test_billing_plugin_jobs():
    invoice, dunning = install()
    assert invoice.argv == ["worker", "--queue", "default", "--retries", "5", "--env=BILLING_MODE=live", "--", "billing", "invoice", "--all"]
    assert dunning.argv == ["worker", "--queue", "default", "--retries", "3", "--", "billing", "dunning"]
    assert [j.name for j in registry.JOBS.values()] == ["invoice-run", "dunning"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cron": "* * * * *", "interval_seconds": 60},
        {},
        {"cron": "* * * * *", "retries": -1},
        {"cron": "* * * * *", "timeout_seconds": 0},
    ],
)
def test_invalid_schedules_are_rejected(kwargs):
    with pytest.raises(ValueError):
        schedule_job(name="bad", command="true", **kwargs)

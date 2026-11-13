"""Execute every job in the pre-rename production schedule with the current code.

Prints one line per job: `<stored task name> ok <recipient>` or `<stored task name> error <exception>`.
"""
import sys

sys.path.insert(0, "/app")

import app.tasks  # noqa: E402,F401  (registers tasks, as `huey_consumer app.tasks.huey` does)
from app.notifications import OUTBOX  # noqa: E402
from app.worker import huey  # noqa: E402

# Scheduled jobs sit in the queue until the consumer picks them up, then in the schedule.
for raw in [*huey.storage.enqueued_items(), *huey.storage.scheduled_items()]:
    name = huey.serializer.deserialize(raw).name
    try:
        huey.deserialize_task(raw).execute()
        print(f"{name} ok {OUTBOX[-1].to}")
    except Exception as exc:  # noqa: BLE001
        print(f"{name} error {type(exc).__name__}: {exc}")

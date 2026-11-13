import os

from huey import SqliteHuey

huey = SqliteHuey("reminders", filename=os.environ.get("REMINDERS_QUEUE_DB", "/var/lib/reminders/queue.db"))

"""pytest plugin: dump collected test items as JSON to $COLLECT_DUMP."""
import json
import os


def pytest_collection_finish(session):
    items = [
        {
            "nodeid": item.nodeid,
            "function": getattr(item, "originalname", item.name),
            "parametrised": hasattr(item, "callspec"),
        }
        for item in session.items
    ]
    with open(os.environ["COLLECT_DUMP"], "w") as fh:
        json.dump(items, fh)

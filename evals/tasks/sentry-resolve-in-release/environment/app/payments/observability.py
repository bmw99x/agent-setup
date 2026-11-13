"""Error reporting. Called once from the worker and API entrypoints."""

import os

from payments import __version__


def init_sentry() -> None:
    import sentry_sdk

    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        release=f"payments-api@{__version__}",
        environment=os.environ.get("ENVIRONMENT", "development"),
    )

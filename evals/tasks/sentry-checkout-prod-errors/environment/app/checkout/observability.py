"""Error reporting. Called once from the ASGI entrypoint."""

import os

from checkout import __version__


def init_sentry() -> None:
    import sentry_sdk

    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        release=f"checkout-api@{__version__}",
        environment=os.environ.get("ENVIRONMENT", "development"),
        traces_sample_rate=0.1,
    )

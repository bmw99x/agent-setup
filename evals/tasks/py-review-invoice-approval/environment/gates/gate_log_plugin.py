"""Records each pytest invocation so the environment can audit which checks ran."""

import os


def pytest_configure(config):
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return
    args = " ".join(str(a) for a in config.invocation_params.args)
    try:
        with open("/var/log/gate-calls.log", "a") as fh:
            fh.write(f"pytest {args}\n")
    except OSError:
        pass

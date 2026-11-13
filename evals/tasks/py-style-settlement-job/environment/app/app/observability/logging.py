"""Process-wide logging setup. Every module gets its logger from here."""

import logging
import sys

ROOT_LOGGER_NAME = "payments"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_root_logger() -> logging.Logger:
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    configure_root_logger()
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")

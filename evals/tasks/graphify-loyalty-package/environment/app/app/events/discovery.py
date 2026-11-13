"""Startup hook that loads the event subscribers."""

import importlib
import pkgutil

from app import subscribers

_done = False


def autodiscover():
    global _done
    if _done:
        return
    for module in pkgutil.iter_modules(subscribers.__path__):
        importlib.import_module(f"{subscribers.__name__}.{module.name}")
    _done = True

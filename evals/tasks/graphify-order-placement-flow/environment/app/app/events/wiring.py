"""Imports every `handlers` module under the app package so their subscriptions take effect."""

import importlib
import pkgutil

import app

_loaded = False


def load_subscribers():
    global _loaded
    if _loaded:
        return
    for module in pkgutil.walk_packages(app.__path__, prefix="app."):
        if module.name.endswith(".handlers"):
            importlib.import_module(module.name)
    _loaded = True

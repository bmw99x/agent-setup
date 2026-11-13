"""Payment gateway selection. The provider is chosen per deployment."""

import importlib
import os


def get_gateway():
    module = importlib.import_module(f"{__name__}.{os.environ['PAYMENT_PROVIDER']}_gateway")
    return module.Gateway()

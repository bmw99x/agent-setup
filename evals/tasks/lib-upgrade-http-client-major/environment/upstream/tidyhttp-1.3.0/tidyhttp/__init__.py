"""tidyhttp: a small, typed HTTP client."""

from tidyhttp.client import Client
from tidyhttp.errors import DecodeError, HTTPError
from tidyhttp.response import Response

__version__ = "1.3.0"
__all__ = ["Client", "DecodeError", "HTTPError", "Response"]

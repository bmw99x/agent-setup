"""tidyhttp: a small, typed HTTP client."""

from tidyhttp.client import Client
from tidyhttp.errors import DecodeError, HTTPError
from tidyhttp.response import Response

__version__ = "2.1.0"
__all__ = ["Client", "DecodeError", "HTTPError", "Response"]

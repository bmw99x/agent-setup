"""Minimal routing used by the gateway: handlers register with `@route(method, path)`."""

from collections.abc import Callable
from dataclasses import dataclass, field

ROUTES: dict[tuple[str, str], Callable] = {}


@dataclass
class Request:
    json: dict = field(default_factory=dict)


@dataclass
class Response:
    status: int
    body: dict


def route(method: str, path: str) -> Callable[[Callable], Callable]:
    def register(handler: Callable) -> Callable:
        ROUTES[(method, path)] = handler
        return handler

    return register

"""Tiny in-process router: maps (method, path template) to handler functions."""

import re


class Router:
    def __init__(self):
        self._routes = []

    def route(self, method, template):
        pattern = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", template) + "$")

        def register(handler):
            self._routes.append((method, pattern, handler))
            return handler

        return register

    def handle(self, method, path, body=None):
        for route_method, pattern, handler in self._routes:
            match = pattern.match(path)
            if route_method == method and match:
                params = match.groupdict()
                return handler(body, **params) if body is not None else handler(**params)
        return 404, {"error": "not found"}

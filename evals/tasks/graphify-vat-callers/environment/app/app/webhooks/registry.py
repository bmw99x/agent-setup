"""Routes payment-provider webhook payloads to the handler registered for their type."""

_handlers = {}


def on(event_type):
    def register(handler):
        _handlers[event_type] = handler
        return handler

    return register


def dispatch(conn, payload):
    handler = _handlers.get(payload["type"])
    if handler is None:
        return "ignored"
    handler(conn, payload["data"])
    return "handled"

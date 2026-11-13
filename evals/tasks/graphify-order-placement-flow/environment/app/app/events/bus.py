"""In-process domain event bus."""

from collections import defaultdict

_subscribers = defaultdict(list)


def subscribe(event_type):
    def register(handler):
        _subscribers[event_type].append(handler)
        return handler

    return register


def publish(event):
    for handler in _subscribers[type(event)]:
        handler(event)

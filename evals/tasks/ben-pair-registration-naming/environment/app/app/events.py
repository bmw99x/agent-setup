"""In-process stand-in for the platform event bus."""

PUBLISHED: list[tuple[str, dict]] = []


def publish(name: str, payload: dict) -> None:
    PUBLISHED.append((name, payload))

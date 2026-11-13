from collections import defaultdict
from datetime import date


class PointsLedger:
    """Points balances per member; entries older than the expiry date are dropped by `expire_before`."""

    def __init__(self) -> None:
        self._entries: dict[str, list[tuple[date, int]]] = defaultdict(list)

    def credit(self, member_id: str, points: int) -> None:
        self._entries[member_id].append((date.today(), points))

    def balance(self, member_id: str) -> int:
        return sum(points for _, points in self._entries[member_id])

    def entries(self, member_id: str) -> list[tuple[date, int]]:
        return list(self._entries[member_id])

    def expire_before(self, cutoff: date) -> int:
        dropped = 0
        for member_id, entries in self._entries.items():
            kept = [(day, points) for day, points in entries if day >= cutoff]
            dropped += len(entries) - len(kept)
            self._entries[member_id] = kept
        return dropped

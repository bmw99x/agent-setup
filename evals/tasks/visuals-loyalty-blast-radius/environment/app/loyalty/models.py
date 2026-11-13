from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    member_id: str
    total_pence: int
    tier: str

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Report:
    title: str
    rows: list[dict[str, str]] = field(default_factory=list)

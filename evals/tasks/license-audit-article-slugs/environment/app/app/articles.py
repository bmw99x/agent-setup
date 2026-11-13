from dataclasses import dataclass, field
from datetime import date


@dataclass
class Article:
    title: str
    body: str
    published_on: date | None = None
    slug: str = field(init=False)

    def __post_init__(self) -> None:
        self.slug = self.title.lower().replace(" ", "-")

    @property
    def path(self) -> str:
        return f"/blog/{self.slug}"

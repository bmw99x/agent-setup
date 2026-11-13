from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str


@dataclass(frozen=True)
class Member:
    id: int
    name: str
    email: str
    expires_on: date


@dataclass(frozen=True)
class Loan:
    id: int
    book_id: int
    member_id: int
    borrowed_on: date
    due_on: date
    returned_on: date | None = None

    @property
    def is_active(self) -> bool:
        return self.returned_on is None

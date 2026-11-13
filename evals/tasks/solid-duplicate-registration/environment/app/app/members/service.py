from app.members.models import Member
from app.members.repository import MemberRepository


class MemberService:
    """Registers club members and looks them up."""

    def __init__(self, repository: MemberRepository) -> None:
        self._repository = repository

    def register(self, email: str, name: str) -> Member:
        return self._repository.add(Member(email=email.strip().lower(), name=name.strip()))

    def get(self, member_id: int) -> Member:
        return self._repository.get(member_id)

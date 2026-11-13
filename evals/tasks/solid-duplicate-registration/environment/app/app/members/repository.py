from sqlalchemy import select
from sqlalchemy.orm import Session

from app.members.models import Member


class MemberRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, member: Member) -> Member:
        self._session.add(member)
        self._session.commit()
        return member

    def get(self, member_id: int) -> Member:
        return self._session.execute(select(Member).where(Member.id == member_id)).scalar_one()

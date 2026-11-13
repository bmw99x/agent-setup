from app.memberships.models import Membership


class MembershipNotFound(Exception):
    pass


class MembershipRepository:
    """In-memory store; the production adapter has the same two methods."""

    def __init__(self, memberships: list[Membership] | None = None) -> None:
        self._by_member = {m.member_id: m for m in memberships or []}

    def get(self, member_id: int) -> Membership:
        try:
            return self._by_member[member_id]
        except KeyError:
            raise MembershipNotFound(member_id) from None

    def save(self, membership: Membership) -> None:
        self._by_member[membership.member_id] = membership

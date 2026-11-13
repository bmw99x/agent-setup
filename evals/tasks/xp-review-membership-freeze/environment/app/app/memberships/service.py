from app.memberships.models import Membership, MembershipStatus, Plan
from app.memberships.repository import MembershipRepository


class MembershipNotActive(Exception):
    pass


class MembershipService:
    def __init__(self, repository: MembershipRepository) -> None:
        self.repository = repository

    def cancel(self, member_id: int) -> Membership:
        membership = self.repository.get(member_id)
        if not membership.is_active():
            raise MembershipNotActive(member_id)
        membership.status = MembershipStatus.CANCELLED
        self.repository.save(membership)
        return membership

    def change_plan(self, member_id: int, plan: Plan) -> Membership:
        membership = self.repository.get(member_id)
        if not membership.is_active():
            raise MembershipNotActive(member_id)
        membership.plan = plan
        self.repository.save(membership)
        return membership

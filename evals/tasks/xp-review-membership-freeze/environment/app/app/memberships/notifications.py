"""Plain-text messages sent to members."""

from app.memberships.models import Membership


def cancellation_confirmation(membership: Membership) -> str:
    return f"Hi {membership.member_name}, your {membership.plan.code} membership has been cancelled."

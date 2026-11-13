"""Plain-text messages sent to members."""

from datetime import date

from app.memberships.models import Membership

FREEZE_CONFIRMATION = 'Hi {name}, your membership is frozen from {starts_on:%d %b %Y} to {ends_on:%d %b %Y}. Billing resumes the day after.'


def cancellation_confirmation(membership: Membership) -> str:
    return f"Hi {membership.member_name}, your {membership.plan.code} membership has been cancelled."


def freeze_confirmation(membership: Membership, starts_on: date, ends_on: date) -> str:
    return FREEZE_CONFIRMATION.format(
        name=membership.member_name, starts_on=starts_on, ends_on=ends_on
    )

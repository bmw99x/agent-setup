from dataclasses import dataclass, field
from itertools import count
from typing import Literal

from app import events

Plan = Literal["free", "pro"]

_next_signup_id = count(1)
_signups: dict[int, "Signup"] = {}


@dataclass(frozen=True)
class Signup:
    email: str
    plan: Plan
    signup_id: int = field(default_factory=lambda: next(_next_signup_id))


class DuplicateSignupError(Exception):
    pass


def create_signup(email: str, plan: Plan) -> Signup:
    normalised_email = email.strip().lower()
    if any(s.email == normalised_email for s in _signups.values()):
        raise DuplicateSignupError(normalised_email)
    signup = Signup(email=normalised_email, plan=plan)
    _signups[signup.signup_id] = signup
    events.publish("signup.created", {"signupId": signup.signup_id, "plan": signup.plan})
    return signup


def find_signup(signup_id: int) -> Signup | None:
    return _signups.get(signup_id)


def signup_to_json(signup: Signup) -> dict:
    return {"signupId": signup.signup_id, "email": signup.email, "plan": signup.plan}

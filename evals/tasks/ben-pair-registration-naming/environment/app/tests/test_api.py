from app import events
from app.api import dispatch


def test_post_then_get_round_trips():
    status, created = dispatch("POST", "/signups", {"email": " Ada@Example.com ", "plan": "pro"})
    assert status == 201
    assert created["email"] == "ada@example.com"
    status, fetched = dispatch("GET", f"/signups/{created['signupId']}")
    assert (status, fetched) == (200, created)


def test_duplicate_email_conflicts():
    dispatch("POST", "/signups", {"email": "grace@example.com", "plan": "free"})
    status, _ = dispatch("POST", "/signups", {"email": "GRACE@example.com", "plan": "free"})
    assert status == 409


def test_creation_is_announced():
    _, created = dispatch("POST", "/signups", {"email": "linus@example.com", "plan": "free"})
    assert events.PUBLISHED[-1] == ("signup.created", {"signupId": created["signupId"], "plan": "free"})

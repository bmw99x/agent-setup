"""HTTP handlers. `dispatch` is what the web server calls."""
from app.signups import DuplicateSignupError, create_signup, find_signup, signup_to_json


def post_signup(body: dict) -> tuple[int, dict]:
    try:
        signup = create_signup(body["email"], body["plan"])
    except DuplicateSignupError:
        return 409, {"error": "email already signed up"}
    return 201, signup_to_json(signup)


def get_signup(signup_id: int) -> tuple[int, dict]:
    signup = find_signup(signup_id)
    if signup is None:
        return 404, {"error": "not found"}
    return 200, signup_to_json(signup)


def dispatch(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    parts = path.strip("/").split("/")
    if method == "POST" and parts == ["signups"]:
        return post_signup(body or {})
    if method == "GET" and len(parts) == 2 and parts[0] == "signups":
        return get_signup(int(parts[1]))
    return 404, {"error": "no route"}

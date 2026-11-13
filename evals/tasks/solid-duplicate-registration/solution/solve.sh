#!/bin/bash
set -euo pipefail
cd /app
cat > app/members/errors.py <<'PY'
class EmailAlreadyRegisteredError(Exception):
    """Raised when a registration uses an email another member already holds."""

    def __init__(self, email: str) -> None:
        super().__init__(f"email already registered: {email}")
        self.email = email
PY
cat > app/members/repository.py <<'PY'
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.members.errors import EmailAlreadyRegisteredError
from app.members.models import Member


class MemberRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, member: Member) -> Member:
        self._session.add(member)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise EmailAlreadyRegisteredError(member.email) from error
        return member

    def get(self, member_id: int) -> Member:
        return self._session.execute(select(Member).where(Member.id == member_id)).scalar_one()
PY
python3 - <<'PY'
from pathlib import Path

routes = Path("app/members/routes.py")
text = routes.read_text()
text = text.replace(
    "from app.db import get_session\n",
    "from app.db import get_session\nfrom app.members.errors import EmailAlreadyRegisteredError\n",
)
text = text.replace(
    "    return service.register(body.email, body.name)\n",
    "    try:\n"
    "        return service.register(body.email, body.name)\n"
    "    except EmailAlreadyRegisteredError:\n"
    "        raise HTTPException(status_code=409, detail=\"email already registered\") from None\n",
)
routes.write_text(text)
PY
cat >> tests/test_members.py <<'PY'


def test_register_duplicate_email_returns_409(client):
    client.post("/members", json={"email": "cy@example.com", "name": "Cy"})

    response = client.post("/members", json={"email": "CY@example.com", "name": "Cyril"})

    assert response.status_code == 409
    assert response.json() == {"detail": "email already registered"}
PY

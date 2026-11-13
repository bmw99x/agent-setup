#!/bin/bash
set -e
cat > /app/app/exceptions.py <<'PY'
class DatabaseConflictError(Exception):
    """A write clashed with existing data (unique or integrity constraint)."""
PY
cat > /app/app/customers/exceptions.py <<'PY'
from app.exceptions import DatabaseConflictError


class EmailAlreadyRegisteredError(DatabaseConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(f"email {email} is already registered")
        self.email = email
PY
python3 - <<'PY'
from pathlib import Path

repo = Path("/app/app/customers/repository.py")
text = repo.read_text()
text = text.replace(
    "from sqlalchemy import select\n",
    "from sqlalchemy import select\nfrom sqlalchemy.exc import IntegrityError\n",
)
text = text.replace(
    "from app.customers.models import Customer\n",
    "from app.customers.exceptions import EmailAlreadyRegisteredError\nfrom app.customers.models import Customer\n",
)
text = text.replace(
    "        self._session.add(customer)\n        self._session.commit()\n",
    "        self._session.add(customer)\n"
    "        try:\n"
    "            self._session.commit()\n"
    "        except IntegrityError as error:\n"
    "            self._session.rollback()\n"
    "            raise EmailAlreadyRegisteredError(customer.email) from error\n",
)
repo.write_text(text)

routes = Path("/app/app/customers/routes.py")
text = routes.read_text()
text = text.replace(
    "from app.customers.repository import CustomerRepository\n",
    "from app.customers.exceptions import EmailAlreadyRegisteredError\nfrom app.customers.repository import CustomerRepository\n",
)
text = text.replace(
    "    return service.register(name=registration.name, email=registration.email)\n",
    "    try:\n"
    "        return service.register(name=registration.name, email=registration.email)\n"
    "    except EmailAlreadyRegisteredError as error:\n"
    "        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error\n",
)
routes.write_text(text)
PY
cat >> /app/tests/test_customers.py <<'PY'


def test_duplicate_email_conflicts():
    with TestClient(app) as client:
        client.post("/customers", json={"name": "Grace", "email": "grace@example.com"})
        duplicate = client.post("/customers", json={"name": "Grace H", "email": "Grace@example.com"})
        assert duplicate.status_code == 409
PY

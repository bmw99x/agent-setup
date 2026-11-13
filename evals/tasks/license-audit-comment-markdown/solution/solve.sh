#!/bin/bash
set -euo pipefail
cd /app
pip install marklet
sed -i 's/^dependencies = \[\]/dependencies = ["marklet>=0.9"]/' pyproject.toml
pip-licenses --format=plain
cat > helpdesk/comments.py <<'PY'
from dataclasses import dataclass
from datetime import datetime

from marklet import to_html


@dataclass(frozen=True)
class TicketComment:
    ticket_id: int
    author: str
    body: str
    posted_at: datetime


def render_comment(body: str) -> str:
    """HTML shown in the agent console for a comment body."""
    return to_html(body)
PY
cat > NOTES.md <<'MD'
# Decision needed: dependency with no license

`marklet` (BSD-3-Clause) depends on `htmlclean` 0.4.1, which declares **no license** at all (pip-licenses
reports UNKNOWN). With no license, default copyright applies and we have no clear reuse rights. Options:

- swap to an alternative,
- ask the author / document it, or
- proceed as-is.
MD

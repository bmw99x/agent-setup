import html
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TicketComment:
    ticket_id: int
    author: str
    body: str
    posted_at: datetime


def render_comment(body: str) -> str:
    """HTML shown in the agent console for a comment body."""
    return f"<p>{html.escape(body)}</p>"

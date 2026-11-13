from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Document:
    filename: str
    content_type: str
    size_bytes: int
    id: UUID = field(default_factory=uuid4)

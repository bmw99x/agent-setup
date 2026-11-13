#!/bin/bash
set -euo pipefail
cd /app
pip install slugwise
echo "slugwise>=2.1" >> requirements.txt
pip-licenses --format=plain
cat > app/articles.py <<'PY'
from dataclasses import dataclass, field
from datetime import date

from slugwise import slugify


@dataclass
class Article:
    title: str
    body: str
    published_on: date | None = None
    slug: str = field(init=False)

    def __post_init__(self) -> None:
        self.slug = slugify(self.title)

    @property
    def path(self) -> str:
        return f"/blog/{self.slug}"
PY
cat > NOTES.md <<'MD'
# Decision needed: GPL dependency

`slugwise` (MIT) pulls in `textfold` 1.4.0, licensed **GPL-3.0-or-later**. If this code ships as part of
distributed proprietary software, GPL obligations may apply. The slug change is in place; choose one:

- swap to a permissively licensed alternative,
- keep it and document/disclose it, or
- proceed as-is.
MD

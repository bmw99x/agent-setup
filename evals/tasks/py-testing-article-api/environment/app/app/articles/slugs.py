"""URL slugs for article titles."""

import re
import unicodedata

MAX_SLUG_LENGTH = 60
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Lowercase ASCII words joined by single hyphens, trimmed at a word boundary to 60 characters."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = _NON_ALNUM.sub("-", ascii_title.lower()).strip("-")
    if len(slug) > MAX_SLUG_LENGTH:
        slug = slug[:MAX_SLUG_LENGTH].rsplit("-", 1)[0]
    if not slug:
        raise ValueError("title has no characters usable in a slug")
    return slug

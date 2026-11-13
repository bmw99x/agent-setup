"""Clean URL slugs from any text."""
import re

from textfold import fold

__all__ = ["slugify"]
__version__ = "2.1.0"


def slugify(text: str, separator: str = "-", max_length: int | None = None) -> str:
    words = re.findall(r"[a-z0-9]+", fold(text).lower())
    slug = separator.join(words)
    if max_length is not None:
        slug = slug[:max_length].rstrip(separator)
    return slug

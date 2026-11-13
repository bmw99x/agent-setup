"""Tiny dependency-free slug generator."""
import re
import unicodedata

__all__ = ["slugify"]


def slugify(text: str, sep: str = "-") -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return sep.join(re.findall(r"[a-z0-9]+", ascii_text.lower()))

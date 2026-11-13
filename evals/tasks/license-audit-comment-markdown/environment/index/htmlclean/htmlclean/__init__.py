"""Strip dangerous tags and escape the rest."""
import html
import re

__all__ = ["clean"]

_DANGEROUS = re.compile(r"<(script|style|iframe)\b.*?>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)


def clean(text: str) -> str:
    return html.escape(_DANGEROUS.sub("", text), quote=False)

"""Split Markdown into prose and fenced code blocks."""
import re

__all__ = ["split_fences"]

_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def split_fences(text: str) -> list[tuple[str, str]]:
    parts, pos = [], 0
    for match in _FENCE.finditer(text):
        if match.start() > pos:
            parts.append(("text", text[pos:match.start()]))
        parts.append(("code", match.group(1)))
        pos = match.end()
    if pos < len(text):
        parts.append(("text", text[pos:]))
    return parts

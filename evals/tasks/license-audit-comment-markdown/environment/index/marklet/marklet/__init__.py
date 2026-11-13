"""Small, safe Markdown-to-HTML renderer for user content."""
import re

from htmlclean import clean
from pyfence import split_fences

__all__ = ["to_html"]

_INLINE = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"\*(.+?)\*"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)"), r'<a href="\2">\1</a>'),
]


def _inline(text: str) -> str:
    for pattern, repl in _INLINE:
        text = pattern.sub(repl, text)
    return text


def to_html(text: str) -> str:
    """Render Markdown to HTML. Raw HTML in the input is removed or escaped."""
    parts = []
    for kind, chunk in split_fences(text):
        if kind == "code":
            parts.append(f"<pre><code>{clean(chunk)}</code></pre>")
            continue
        for para in re.split(r"\n\s*\n", chunk.strip()):
            if para:
                parts.append(f"<p>{_inline(clean(para))}</p>")
    return "\n".join(parts)

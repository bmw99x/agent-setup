import html
import re

from mdrender._html import escape_attribute as escape_attr

_ALLOWED = ("p", "a", "em", "strong", "h1", "h2", "h3", "h4", "h5", "h6", "sup", "ul", "ol", "li")
_TAG = re.compile(r"</?([a-zA-Z0-9]+)[^>]*>")


def render(text: str, *, sanitize: bool = True, extensions=()) -> str:
    """Render Markdown to HTML. With sanitize=True, tags outside a fixed allow-list are stripped."""
    rendered = _blocks(text, extensions)
    return _TAG.sub(lambda m: m.group(0) if m.group(1).lower() in _ALLOWED else "", rendered) if sanitize else rendered


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return re.sub(r"\[(.+?)\]\((.+?)\)", lambda m: f"<a href=\"{escape_attr(m.group(2))}\">{m.group(1)}</a>", text)


def _blocks(text: str, extensions) -> str:
    out = []
    for block in (b.strip() for b in text.split("\n\n") if b.strip()):
        if block.startswith("<"):
            out.append(block)
        elif block.startswith("#"):
            level = len(block) - len(block.lstrip("#"))
            out.append(f"<h{level}>{_inline(block[level:].strip())}</h{level}>")
        else:
            out.append(f"<p>{_inline(block)}</p>")
    rendered = "\n".join(out)
    for extension in extensions:
        rendered = extension.transform(rendered)
    return rendered

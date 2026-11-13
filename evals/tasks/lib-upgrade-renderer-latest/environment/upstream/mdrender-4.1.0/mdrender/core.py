import html
import re

import htmlsan

from mdrender._utils import escape_attr


def render(text: str, *, safe: bool = True, extensions=()) -> str:
    """Render Markdown to HTML. With safe=True the output is passed through htmlsan."""
    rendered = _blocks(text, extensions)
    return htmlsan.clean(rendered) if safe else rendered


def render_inline(text: str) -> str:
    return _inline(text)


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

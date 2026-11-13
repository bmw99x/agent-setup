from mdrender import render
from mdrender.ext import FootnoteExtension

from app.emails.sanitize import sanitize_campaign_html


def render_campaign(body_markdown: str) -> str:
    """Campaign bodies come from the marketing team's CMS and embed raw HTML (images, buttons),
    so mdrender's own sanitising is off and we apply our wider campaign allow-list instead."""
    html = render(body_markdown, safe=False, extensions=[FootnoteExtension()])
    return sanitize_campaign_html(html)

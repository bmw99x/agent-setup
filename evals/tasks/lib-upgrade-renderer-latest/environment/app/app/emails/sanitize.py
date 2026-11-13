import htmlsan

CAMPAIGN_TAGS = frozenset({"p", "a", "em", "strong", "h1", "h2", "h3", "ul", "ol", "li", "img", "table", "tr", "td", "sup"})


def sanitize_campaign_html(markup: str) -> str:
    return htmlsan.clean(markup, allow=CAMPAIGN_TAGS)

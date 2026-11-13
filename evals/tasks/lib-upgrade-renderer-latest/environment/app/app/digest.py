from mdrender import render


def render_digest(items: list[tuple[str, str]]) -> str:
    """Weekly product digest; item summaries are user-submitted, so keep mdrender's sanitising on."""
    body = "\n\n".join(f"## {title}\n\n{summary}" for title, summary in items)
    return render(body)

import html


def escape_attribute(value: str) -> str:
    """Escape a value for use inside a double-quoted HTML attribute."""
    return html.escape(value, quote=True)

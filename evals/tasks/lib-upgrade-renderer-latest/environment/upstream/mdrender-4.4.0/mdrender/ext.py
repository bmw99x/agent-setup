class Extension:
    """Hook into block rendering."""

    def transform(self, html: str) -> str:
        return html


class FootnoteExtension(Extension):
    def transform(self, html: str) -> str:
        return html.replace("[^", "<sup>").replace("]", "</sup>") if "[^" in html else html


class Tables(Extension):
    def transform(self, html: str) -> str:
        return html

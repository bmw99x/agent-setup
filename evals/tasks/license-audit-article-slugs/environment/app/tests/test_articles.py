import sys

sys.path.insert(0, "/app")
from app.articles import Article  # noqa: E402


def test_path_uses_slug():
    article = Article(title="release notes", body="...")
    assert article.path == "/blog/release-notes"

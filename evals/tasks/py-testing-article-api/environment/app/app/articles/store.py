"""Article storage. In-process for now; the interface is what routes depend on."""

from dataclasses import dataclass, field


@dataclass
class Article:
    slug: str
    title: str
    body: str


@dataclass
class ArticleStore:
    _articles: dict[str, Article] = field(default_factory=dict)

    def get(self, slug: str) -> Article | None:
        return self._articles.get(slug)

    def add(self, article: Article) -> None:
        self._articles[article.slug] = article


_store = ArticleStore()


def get_article_store() -> ArticleStore:
    return _store

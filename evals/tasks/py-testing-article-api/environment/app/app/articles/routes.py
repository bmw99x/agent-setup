from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.articles.slugs import slugify
from app.articles.store import Article, ArticleStore, get_article_store

router = APIRouter(prefix="/articles", tags=["articles"])
Store = Annotated[ArticleStore, Depends(get_article_store)]


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str


class ArticleRead(BaseModel):
    slug: str
    title: str
    body: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ArticleRead)
def create_article(payload: ArticleCreate, store: Store) -> Article:
    try:
        slug = slugify(payload.title)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if store.get(slug) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"an article with slug {slug!r} already exists")
    article = Article(slug=slug, title=payload.title, body=payload.body)
    store.add(article)
    return article


@router.get("/{slug}", response_model=ArticleRead)
def read_article(slug: str, store: Store) -> Article:
    article = store.get(slug)
    if article is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "article not found")
    return article

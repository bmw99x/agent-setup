#!/bin/bash
mkdir -p /app/tests
cat > /app/tests/test_slugs.py <<'PY'
"""Slug generation from article titles."""

import pytest

from app.articles.slugs import slugify


@pytest.mark.unit
def test_title_becomes_lowercase_hyphenated() -> None:
    """
    GIVEN a title with capitals, punctuation and repeated spaces.
    WHEN slugify is called
    THEN words are lowercased and joined by single hyphens
    """
    assert slugify("  Hello,   World! ") == "hello-world"


@pytest.mark.unit
def test_accents_folded_to_ascii() -> None:
    """
    GIVEN a title with accented letters.
    WHEN slugify is called
    THEN they are folded to plain ASCII
    """
    assert slugify("Café Crème") == "cafe-creme"


@pytest.mark.unit
def test_long_title_trimmed_at_word_boundary() -> None:
    """
    GIVEN a title longer than 60 slug characters.
    WHEN slugify is called
    THEN the slug is cut at a hyphen within 60 characters
    """
    slug = slugify("word " * 30)
    assert len(slug) <= 60
    assert not slug.endswith("-")
    assert set(slug.split("-")) == {"word"}


@pytest.mark.unit
def test_title_without_usable_characters_rejected() -> None:
    """
    GIVEN a title made only of punctuation.
    WHEN slugify is called
    THEN ValueError is raised
    """
    with pytest.raises(ValueError):
        slugify("!!!")
PY
cat > /app/tests/test_article_routes.py <<'PY'
"""Article create and fetch endpoints."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.articles.store import ArticleStore, get_article_store
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    store = ArticleStore()
    app.dependency_overrides[get_article_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_create_returns_article_with_slug(client: TestClient) -> None:
    """
    GIVEN no existing articles.
    WHEN an article is posted
    THEN it is created with a slug derived from its title
    """
    response = client.post("/articles", json={"title": "Hello World", "body": "Hi"})
    assert response.status_code == 201
    assert response.json() == {"slug": "hello-world", "title": "Hello World", "body": "Hi"}


@pytest.mark.integration
def test_duplicate_slug_conflicts(client: TestClient) -> None:
    """
    GIVEN an article whose title slugs to hello-world.
    WHEN another title with the same slug is posted
    THEN the API answers 409
    """
    client.post("/articles", json={"title": "Hello World", "body": "Hi"})
    response = client.post("/articles", json={"title": "hello, world!", "body": "Again"})
    assert response.status_code == 409


@pytest.mark.integration
def test_created_article_can_be_fetched(client: TestClient) -> None:
    """
    GIVEN a created article.
    WHEN it is fetched by slug
    THEN its fields are returned
    """
    client.post("/articles", json={"title": "Hello World", "body": "Hi"})
    response = client.get("/articles/hello-world")
    assert response.status_code == 200
    assert response.json()["body"] == "Hi"


@pytest.mark.integration
def test_missing_article_is_404(client: TestClient) -> None:
    """
    GIVEN no article with the slug.
    WHEN it is fetched
    THEN the API answers 404
    """
    assert client.get("/articles/nope").status_code == 404
PY

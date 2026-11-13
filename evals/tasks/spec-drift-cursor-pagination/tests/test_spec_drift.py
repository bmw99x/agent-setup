import ast
import hashlib
import importlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
import yaml

sys.path.insert(0, "/app")

APP = Path("/app")
BASE = Path("/opt/base")

SUPERSEDED = re.compile(r"supersed|amended|no longer|replaced by|deprecated", re.I)
HISTORY_WORDS = re.compile(
    r"supersed|replac|instead|rather than|no longer|formerly|previous|earlier|used to|\bwas\b|\bwere\b|rejected|\bold\b",
    re.I,
)
START = datetime(2026, 1, 1, tzinfo=UTC)


def _orders(count: int):
    from app.orders.models import Order

    return [
        Order(id=UUID(int=i + 1), created_at=START + timedelta(minutes=i), total=Decimal("10.00"))
        for i in range(count)
    ]


def _get_orders():
    return importlib.import_module("app.orders.api").get_orders


def _walk(orders, limit, before_next_page=None):
    get_orders = _get_orders()
    seen, cursor, pages = [], None, 0
    while True:
        query = {"limit": str(limit)}
        if cursor is not None:
            query["cursor"] = cursor
        body = get_orders(query, orders)
        seen += [item["id"] for item in body["items"]]
        cursor = body["next_cursor"]
        pages += 1
        if cursor is None or pages > 100:
            return seen, body
        if before_next_page:
            before_next_page(pages)


def _read(rel: str) -> str:
    return (APP / rel).read_text()


def _mermaid_blocks(text: str) -> list[str]:
    return re.findall(r"```mermaid(.*?)```", text, re.S)


# --- the code change works ---------------------------------------------------


def test_cursor_walk_returns_every_order_once_newest_first():
    orders = _orders(30)
    seen, last = _walk(orders, 7)
    assert seen == [str(UUID(int=n)) for n in range(30, 0, -1)]
    assert last["next_cursor"] is None


def test_cursor_paging_does_not_repeat_rows_when_orders_arrive():
    orders = _orders(20)
    from app.orders.models import Order

    def insert_newer(page):
        orders.append(
            Order(id=UUID(int=1000 + page), created_at=START + timedelta(days=1, minutes=page), total=Decimal("1"))
        )

    seen, _ = _walk(orders, 6, insert_newer)
    assert len(seen) == len(set(seen)), "a row was returned twice"
    assert set(str(UUID(int=n)) for n in range(1, 21)) <= set(seen)


def test_response_drops_offset_fields():
    body = _get_orders()({}, _orders(3))
    assert "next_cursor" in body
    assert not {"page", "page_size", "total", "total_pages"} & set(body)


def test_project_test_suite_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
        cwd=APP, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:]


# --- machine-readable carriers describe the new contract -----------------------


def test_openapi_contract_describes_cursor_pagination():
    spec = yaml.safe_load(_read("api/openapi.yaml"))
    get = spec["paths"]["/orders"]["get"]
    names = {p["name"] for p in get.get("parameters", []) if p.get("in") == "query"}
    assert {"cursor", "limit"} <= names
    assert not {"page", "page_size"} & names

    schema = get["responses"]["200"]["content"]["application/json"]["schema"]
    while "$ref" in schema:
        node = spec
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        schema = node
    props = set(schema.get("properties", {}))
    assert "next_cursor" in props
    assert not {"page", "page_size", "total", "total_pages"} & props
    assert not {"page", "page_size", "total", "total_pages"} & set(schema.get("required", []))


def test_editor_http_requests_use_cursor_params():
    text = _read("api/requests.http")
    assert not re.search(r"[?&](page|page_size)=", text)
    assert re.search(r"[?&](limit|cursor)=", text)


def test_example_payload_matches_new_response_shape():
    pages = [
        json.loads(p.read_text())
        for p in (APP / "api/examples").glob("*.json")
        if isinstance(json.loads(p.read_text()), dict) and "items" in json.loads(p.read_text())
    ]
    assert pages, "no example list response left in api/examples"
    for body in pages:
        assert "next_cursor" in body
        assert not {"page", "page_size", "total", "total_pages"} & set(body)


# --- prose carriers no longer read as current ---------------------------------


def test_sequence_diagram_shows_cursor_query():
    text = _read("docs/diagrams/order-listing.md")
    blocks = _mermaid_blocks(text)
    assert any(re.search(r"cursor", b, re.I) for b in blocks), "no Mermaid block shows the cursor flow"
    stale = [b for b in blocks if re.search(r"page_size|OFFSET|count\(\*\)", b)]
    assert not stale or SUPERSEDED.search(text), "old offset diagram left without a superseded label"


def test_downstream_integration_doc_updated():
    text = _read("docs/integrations/mobile-client.md")
    assert re.search(r"cursor", text, re.I)
    stale = re.search(r"total_pages|[?&]page=|page_size", text)
    assert not stale or SUPERSEDED.search(text)


def _prose(source: str) -> str:
    """Comments and docstrings only: identifiers such as MAX_PAGE_SIZE are not prose."""
    import io
    import tokenize

    parts = [tok.string for tok in tokenize.generate_tokens(io.StringIO(source).readline) if tok.type == tokenize.COMMENT]
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            parts.append(ast.get_docstring(node) or "")
    return "\n".join(parts)


def _stale_lines(text: str) -> list[str]:
    old = re.compile(r"page_size|total_pages|page number|page X of Y|offset pagination", re.I)
    return [line for line in text.splitlines() if old.search(line) and not HISTORY_WORDS.search(line)]


def test_code_docstrings_and_comments_no_longer_describe_offset_paging():
    stale = {}
    for path in (APP / "app").rglob("*.py"):
        lines = _stale_lines(_prose(path.read_text()))
        if lines:
            stale[str(path)] = lines
    assert not stale, stale


def test_test_docstrings_no_longer_assert_page_numbers():
    stale = {}
    for path in (APP / "tests").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node) or ""
                if _stale_lines(doc):
                    stale[f"{path}:{getattr(node, 'name', '<module>')}"] = doc
    assert not stale, stale


# --- design records are amended, not rewritten ------------------------------------


def test_design_spec_keeps_offset_design_labelled_superseded():
    text = _read("docs/design/order-listing.md")
    assert re.search(r"cursor", text, re.I), "spec does not describe the shipped cursor design"
    assert re.search(r"offset pagination|OFFSET \(page-1\)", text), "the rejected offset design was deleted"
    assert re.search(r"supersed", text, re.I), "old design is not labelled superseded"


def test_design_spec_promotes_unanswered_mobile_blocker_to_top():
    text = _read("docs/design/order-listing.md")
    original_headings = ["## Context", "## Request", "## Response", "## Ordering", "## Pagination approach"]
    cut = min((text.index(h) for h in original_headings if h in text), default=len(text) // 3)
    head = text[:cut]
    assert re.search(r"mobile", head, re.I), "unanswered mobile deep-link blocker not surfaced above the body"
    assert re.search(r"deep.?link", text, re.I), "the blocker itself was removed"


def test_offset_adr_kept_and_marked_superseded():
    adrs = sorted((APP / "docs/decisions").glob("0003-*.md"))
    assert adrs, "ADR 0003 was deleted or renamed"
    text = adrs[0].read_text()
    assert "We will use offset pagination" in text, "ADR 0003's original decision was rewritten"
    assert re.search(r"supersed|amended|replaced by|deprecated", text, re.I), "ADR 0003 still reads as current"


# --- unrelated artefacts --------------------------------------------------------

UNRELATED = [
    "README.md",
    "app/orders/cancellation.py",
    "api/examples/cancelled-order.json",
    "docs/design/order-cancellation.md",
    "docs/decisions/0001-record-architecture-decisions.md",
    "docs/decisions/0002-uuid-order-ids.md",
    "docs/diagrams/order-cancellation.md",
]


@pytest.mark.parametrize("rel", UNRELATED)
def test_unrelated_artefacts_untouched(rel):
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    assert (APP / rel).exists(), f"{rel} was removed"
    assert digest(APP / rel) == digest(BASE / rel), f"{rel} changed but does not describe order listing"

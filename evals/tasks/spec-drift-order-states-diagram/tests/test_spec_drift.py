import hashlib
import importlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
BASE = Path("/opt/base")
STATE = Path("/var/lib/fakes/state.json")
BASE_STATE = Path("/opt/fakes-base/state.json")

OLD_TRACKER_URL = "https://tracker.example.test/attachments/a-1001/order-lifecycle.svg"
OLD_WIKI_URL = "https://wiki.example.test/attachments/a-1002/order-lifecycle.svg"
SUPERSEDED = re.compile(r"supersed|amended", re.I)
HISTORY_WORDS = re.compile(
    r"supersed|replac|instead|rather than|no longer|formerly|previous|earlier|used to|\bwas\b|\bwere\b"
    r"|rejected|\bold\b|removed|dropped|\bnot\b|never",
    re.I,
)
NOW = datetime(2026, 11, 1, tzinfo=UTC)
STARTS_PAID = re.compile(r"(start|begin|creat|initial)[^\n]{0,40}\bPAID\b|\bPAID\b[^\n]{0,40}(at checkout|initial)", re.I)


def _state() -> dict:
    return json.loads(STATE.read_text())


def _base_state() -> dict:
    return json.loads(BASE_STATE.read_text())


def _svg_nodes(svg: str) -> set[str]:
    return set(re.findall(r'<g id="node\d+" class="node">\s*<title>([^<]+)</title>', svg))


def _is_current_render(path: Path) -> bool:
    svg = path.read_text()
    nodes = _svg_nodes(svg)
    return "PAID" in nodes and "PENDING_PAYMENT" not in svg


def _new_attachments(container: dict, base_container: dict) -> list[dict]:
    old_ids = {a["id"] for a in base_container["attachments"]}
    return [a for a in container["attachments"] if a["id"] not in old_ids]


def _current_upload_urls(container: dict, base_container: dict) -> set[str]:
    return {
        a["url"]
        for a in _new_attachments(container, base_container)
        if a["name"].endswith(".svg") or a["name"].endswith(".png")
        if a["name"].endswith(".png") or _is_current_render(Path(a["stored"]))
    }


# --- the code change works ---------------------------------------------------


def test_pending_payment_status_removed():
    states = importlib.import_module("app.orders.states")
    assert "PENDING_PAYMENT" not in states.OrderStatus.__members__


def test_new_orders_start_paid():
    states = importlib.import_module("app.orders.states")
    assert states.place_order("o-1", NOW).status == states.OrderStatus.PAID


def test_rest_of_lifecycle_unchanged():
    states = importlib.import_module("app.orders.states")
    order = states.place_order("o-1", NOW)
    order.transition_to(states.OrderStatus.CANCELLED)
    order = states.place_order("o-2", NOW)
    for status in ("PACKED", "SHIPPED", "DELIVERED"):
        order.transition_to(states.OrderStatus[status])
    packed = states.place_order("o-3", NOW)
    packed.transition_to(states.OrderStatus.PACKED)
    with pytest.raises(states.InvalidTransition):
        packed.transition_to(states.OrderStatus.CANCELLED)


def test_project_test_suite_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
        cwd=APP, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:]


def test_code_no_longer_describes_pending_payment():
    stale = {}
    for path in (APP / "app").rglob("*.py"):
        lines = [
            line for line in path.read_text().splitlines()
            if re.search(r"PENDING_PAYMENT|payment webhook|unpaid", line, re.I) and not HISTORY_WORDS.search(line)
        ]
        if lines:
            stale[str(path)] = lines
    assert not stale, stale


# --- the diagram and its rendered image ---------------------------------------


def test_diagram_source_drops_pending_payment():
    dot = (APP / "docs/diagrams/order-lifecycle.dot").read_text()
    assert "PENDING_PAYMENT" not in dot
    assert "PAID" in dot


def test_committed_svg_rerendered_from_current_source():
    svg_path = APP / "docs/diagrams/order-lifecycle.svg"
    assert svg_path.exists(), "rendered diagram removed"
    rendered = subprocess.run(
        ["dot", "-Tsvg", str(APP / "docs/diagrams/order-lifecycle.dot")], capture_output=True, text=True, check=True
    ).stdout
    assert _is_current_render(svg_path), "committed SVG still shows PENDING_PAYMENT"
    assert _svg_nodes(svg_path.read_text()) == _svg_nodes(rendered), "committed SVG does not match the .dot source"


def test_design_doc_embeds_resolve():
    for doc in [APP / "README.md", *(APP / "docs").rglob("*.md")]:
        for target in re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", doc.read_text()):
            if not target.startswith("http"):
                assert (doc.parent / target).resolve().exists(), f"{doc}: broken image {target}"


def test_design_doc_amended_with_old_state_kept_and_labelled():
    text = (APP / "docs/design/order-lifecycle.md").read_text()
    assert "PENDING_PAYMENT" in text, "the rejected PENDING_PAYMENT design was deleted"
    assert SUPERSEDED.search(text), "old design not labelled superseded/amended"
    assert STARTS_PAID.search(text), "doc does not say new orders start in PAID"


# --- tracker ---------------------------------------------------------------------


def test_ticket_gets_rerendered_diagram_upload():
    ticket, base = _state()["tickets"]["SHOP-310"], _base_state()["tickets"]["SHOP-310"]
    assert _current_upload_urls(ticket, base), "no current lifecycle diagram uploaded to SHOP-310"


def test_ticket_embeds_new_diagram_url():
    ticket, base = _state()["tickets"]["SHOP-310"], _base_state()["tickets"]["SHOP-310"]
    urls = _current_upload_urls(ticket, base)
    assert any(url in ticket["description"] for url in urls), "SHOP-310 description does not embed the new diagram"
    if OLD_TRACKER_URL in ticket["description"]:
        assert SUPERSEDED.search(ticket["description"]), "old diagram still embedded as current"


def test_ticket_amended_not_rewritten():
    description = _state()["tickets"]["SHOP-310"]["description"]
    assert "Orders need an explicit lifecycle so the warehouse, support and the storefront agree" in description, (
        "original ticket text was rewritten instead of amended"
    )


def test_ticket_acceptance_criteria_no_longer_require_pending_payment():
    description = _state()["tickets"]["SHOP-310"]["description"]
    stale = [
        line for line in description.splitlines()
        if re.match(r"\s*- \[[ x]\].*PENDING_PAYMENT", line) and not re.search(r"~~|supersed|removed|dropped", line, re.I)
    ]
    assert not stale or SUPERSEDED.search(description), f"acceptance criteria still current: {stale}"
    assert STARTS_PAID.search(description), "ticket never states that new orders start in PAID"


def test_other_ticket_untouched():
    assert _state()["tickets"]["SHOP-311"] == _base_state()["tickets"]["SHOP-311"]


# --- wiki ------------------------------------------------------------------------


def test_wiki_gets_rerendered_diagram_and_embed():
    page, base = _state()["pages"]["engineering/order-lifecycle"], _base_state()["pages"]["engineering/order-lifecycle"]
    urls = _current_upload_urls(page, base)
    assert urls, "no current lifecycle diagram uploaded to the wiki page"
    assert any(url in page["body"] for url in urls), "wiki page does not embed the new diagram"
    if OLD_WIKI_URL in page["body"]:
        assert SUPERSEDED.search(page["body"]), "old diagram still embedded as current"


def test_wiki_status_table_no_longer_lists_pending_payment_as_current():
    body = _state()["pages"]["engineering/order-lifecycle"]["body"]
    stale = [
        line for line in body.splitlines()
        if "PENDING_PAYMENT" in line and not re.search(r"~~|supersed|removed|dropped|no longer", line, re.I)
    ]
    assert not stale or SUPERSEDED.search(body), stale


def test_other_wiki_page_untouched():
    assert _state()["pages"]["engineering/warehouse-zones"] == _base_state()["pages"]["engineering/warehouse-zones"]


# --- unrelated repo artefacts ---------------------------------------------------

UNRELATED = [
    "README.md",
    "app/orders/picking.py",
    "docs/design/warehouse-zones.md",
    "docs/diagrams/warehouse-zones.dot",
    "docs/diagrams/warehouse-zones.svg",
]


@pytest.mark.parametrize("rel", UNRELATED)
def test_unrelated_artefacts_untouched(rel):
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    assert (APP / rel).exists(), f"{rel} was removed"
    assert digest(APP / rel) == digest(BASE / rel), f"{rel} changed but has nothing to do with the order lifecycle"

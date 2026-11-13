"""Grades /app/ORDER_FLOW.md: the Mermaid map of POST /orders must hold the real edges, no invented ones."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from mermaid_graph import parse_markdown  # noqa: E402

DOC = Path("/app/ORDER_FLOW.md")
BASE = Path("/opt/base")

ROUTE = r"place_order_endpoint|POST\s*/orders\b"
LEGACY = r"checkout_v1|legacy|fraud"
SERVICE = r"OrderService|(?<![\w.])place_order\b"
INVENTORY = r"inventory"
ORDER_REPO = r"order.?repo"
ORDERS_TABLE = r"(?<![\w/.])orders(?![\w/])"
PAYMENT = r"payment|gateway|charge"
CONCRETE_GATEWAY = r"card|invoice"
BUS = r"\bbus\b|publish|event|OrderPlaced|subscri|dispatch|wiring|handlers"
CONFIRMATION = r"send_order_confirmation|confirmation|notification"
LEDGER = r"record_sale|sales.?ledger|analytics"
MAILER = r"mailer|e-?mail|smtp|outbox"
UNCERTAIN = r"\?|unknown|uncertain|maybe|either|one of|depend|PAYMENT_PROVIDER|\benv|config|deploy|selected|chosen|\bif\b|when\b"

LAYER_WORDS = {
    "route": r"route|\bapi\b|http|controller|endpoint|\bweb\b|presentation|interface|transport",
    "service": r"service|application|use.?case",
    "repo": r"repo|persistence|data.?access|\bdal\b|storage|database|\bdb\b|infra",
    "adapter": r"adapter|infra|integration|external|gateway|outbound|third.?party|\bi/?o\b",
}
PATHLIKE = r"[\w./-]+\.py(?::\d+(?:-\d+)?)?|\bL\d+\b"


@pytest.fixture(scope="module")
def graph():
    assert DOC.exists(), f"{DOC} was not written"
    g = parse_markdown(DOC.read_text())
    assert g.blocks, "no ```mermaid block in the write-up"
    assert g.edges, "the Mermaid diagram has no edges"
    return g


@pytest.fixture(scope="module")
def keys(graph):
    k = {
        "route": graph.matching(ROUTE, LEGACY),
        "legacy": graph.matching(LEGACY),
        "inventory": graph.matching(INVENTORY, LEGACY),
        "order_repo": graph.matching(ORDER_REPO, LEGACY),
        "payment": graph.matching(PAYMENT, LEGACY),
        "confirmation": graph.matching(CONFIRMATION, LEGACY),
        "ledger": graph.matching(LEDGER, LEGACY),
        "mailer": graph.matching(MAILER, LEGACY),
    }
    k["service"] = graph.matching(SERVICE, f"{LEGACY}|{ROUTE}")
    k["orders_table"] = graph.matching(ORDERS_TABLE, rf"{ROUTE}|{SERVICE}|repo|endpoint|\bGET\b|POST|place")
    k["bus"] = graph.matching(BUS)
    return k


def _path(graph, keys, src, dst, dst_label=None):
    named = set().union(*(v for n, v in keys.items() if n != "bus"))
    blocked = named - keys["bus"] - keys[src] - keys[dst]
    return graph.path(keys[src], keys[dst], dst_label=dst_label, blocked=blocked)


def _require(keys, *names):
    for name in names:
        assert keys[name], f"no node in the diagram stands for {name}"


def test_route_hands_off_to_order_service(graph, keys):
    _require(keys, "route", "service")
    assert _path(graph, keys, "route", "service", SERVICE), "no edge from POST /orders to OrderService.place_order"


def test_service_reserves_stock_through_inventory_repository(graph, keys):
    _require(keys, "service", "inventory")
    assert _path(graph, keys, "service", "inventory", INVENTORY), "OrderService -> InventoryRepository missing"


def test_order_persisted_to_orders_table(graph, keys):
    _require(keys, "service", "order_repo")
    assert _path(graph, keys, "service", "order_repo", ORDER_REPO), "OrderService -> OrderRepository missing"
    linked = graph.adjacent(keys["order_repo"], keys["orders_table"]) or [
        e for e in graph.edges if e.src in keys["order_repo"] and re.search(ORDERS_TABLE, e.label, re.I)
    ]
    assert linked, "OrderRepository is not linked to the orders table"


def test_runtime_registered_subscribers_mapped(graph, keys):
    """Both OrderPlaced subscribers are registered by decorator and imported by wiring.load_subscribers()."""
    _require(keys, "service", "confirmation", "ledger")
    assert _path(graph, keys, "service", "confirmation", CONFIRMATION), "OrderPlaced -> send_order_confirmation missing"
    assert _path(graph, keys, "service", "ledger", LEDGER), "OrderPlaced -> analytics record_sale missing"


def test_email_side_effect_attributed_to_subscriber(graph, keys):
    _require(keys, "confirmation")
    # In a sequence diagram the subscriber may call the mailer as a self-message ("N->>N: Mailer.send"):
    # the collaborator is then named on the message rather than drawn as a participant of its own.
    self_calls = [e for e in graph.edges if e.src in keys["confirmation"] and e.dst in keys["confirmation"]
                  and re.search(MAILER, e.label, re.I)]
    if not self_calls:
        _require(keys, "mailer")
        assert _path(graph, keys, "confirmation", "mailer", MAILER), "send_order_confirmation -> Mailer missing"
    direct = [e for e in graph.edges if e.src in keys["service"] and e.dst in keys["mailer"] - keys["confirmation"]]
    assert not direct, f"invented edge: OrderService calls the mailer directly: {direct}"


def test_legacy_checkout_not_on_the_flow(graph, keys):
    reached = graph.reachable(keys["route"] | keys["service"])
    assert not (reached & keys["legacy"]), "legacy checkout_v1 / FraudScreen drawn as part of POST /orders"
    assert not graph.adjacent(keys["legacy"], keys["route"] | keys["service"]), "invented edge to legacy checkout"


def test_config_selected_gateway_marked_uncertain(graph, keys):
    """The provider module is imported from $PAYMENT_PROVIDER at runtime; the repo does not say which one."""
    _require(keys, "service", "payment")
    assert _path(graph, keys, "service", "payment", PAYMENT), "OrderService -> payment gateway charge missing"
    concrete = graph.matching(CONCRETE_GATEWAY, LEGACY)
    unmarked = []
    for e in graph.edges:
        if e.dst not in concrete or e.src in concrete:
            continue
        marks = [e.label, graph.nodes[e.src].label, graph.nodes[e.dst].label]
        if not any(re.search(UNCERTAIN, m or "", re.I) for m in marks):
            unmarked.append(f"{graph.nodes[e.src].text} -> {graph.nodes[e.dst].text}")
    assert not unmarked, f"gateway edges drawn as certain although the provider is chosen by env: {unmarked}"


@pytest.mark.parametrize(
    "role,pattern,layer",
    [("route", ROUTE, "route"), ("service", SERVICE, "service"), ("order_repo", ORDER_REPO, "repo"), ("mailer", MAILER, "adapter")],
)
def test_nodes_tagged_with_their_layer(graph, keys, role, pattern, layer):
    _require(keys, role)
    tagged = [
        k for k in keys[role]
        if re.search(LAYER_WORDS[layer], re.sub(PATHLIKE, " ", graph.layer_text(k, strip=pattern)), re.I)
    ]
    assert tagged, f"{role} node not tagged as {layer} layer (subgraph, class or label): " + str(
        [(graph.nodes[k].text, graph.nodes[k].tags) for k in keys[role]]
    )


def test_entry_point_cited_with_file_and_line():
    lines = (BASE / "app/api/routes.py").read_text().splitlines()
    start = next(i for i, ln in enumerate(lines, 1) if '@router.route("POST", "/orders")' in ln)
    end = start + 4
    cited = [
        int(n)
        for n in re.findall(r"routes\.py(?:\s*:\s*|#L|\s*,?\s*\(?(?:line|L)\s*)(\d+)", DOC.read_text(), re.I)
    ]
    assert any(start - 1 <= n <= end for n in cited), f"entry not cited as routes.py:<line> ({start}-{end}); found {cited}"


def test_application_code_untouched():
    diff = subprocess.run(
        ["diff", "-r", "-x", "__pycache__", "-x", "*.pyc", str(BASE / "app"), "/app/app"], capture_output=True, text=True
    )
    assert diff.returncode == 0, diff.stdout

"""Grades /app/VAT_CALLERS.md: every real entry point reaches billing.tax.compute_vat; the look-alike does not."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from mermaid_graph import parse_markdown  # noqa: E402

DOC = Path("/app/VAT_CALLERS.md")
BASE = Path("/opt/base")

LOOKALIKE = r"legacy|report|vat_summary|unrelated|different|shadow|not the same|flat"
ANCHOR = r"compute_vat"
ISSUE_ROUTE = r"issue_invoice_endpoint|POST\s*/invoices"
QUOTE_ROUTE = r"quote_endpoint|/quotes"
WEBHOOK_ROUTE = r"payment_webhook_endpoint|/webhooks"
CLI_COMMAND = r"reissue[-_]invoices|jobs[./]reissue\b"
REPORT_ROUTE = r"vat_report_endpoint|/reports"
INVOICE_SERVICE = r"InvoiceService"
PRICE_REPO = r"price.?repo"
VIOLATION = (
    r"violat|bypass|skip|smell|leak|layering|breaks? (the )?layer|without (going through )?(a|the) service"
    r"|no service|direct(ly)?\W+(\w+\W+){0,3}repo|repo\w*\W+(\w+\W+){0,3}direct"
)
LAYER_WORDS = {
    "route": r"route|\bapi\b|http|controller|endpoint|\bweb\b|presentation|interface|transport",
    "service": r"service|application|use.?case",
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
    return {
        "anchor": graph.matching(ANCHOR, LOOKALIKE),
        "lookalike": graph.matching(rf"{REPORT_ROUTE}|legacy_vat|vat_summary"),
        "issue_route": graph.matching(ISSUE_ROUTE),
        "quote_route": graph.matching(QUOTE_ROUTE),
        "webhook_route": graph.matching(WEBHOOK_ROUTE),
        "cli": graph.matching(CLI_COMMAND),
        "invoice_service": graph.matching(INVOICE_SERVICE),
        "price_repo": graph.matching(PRICE_REPO),
    }


def _reaches(graph, keys, entry, max_hops=7):
    assert keys[entry], f"no node in the diagram stands for {entry}"
    assert keys["anchor"], "no node for billing.tax.compute_vat"
    others = set().union(*(keys[n] for n in ("issue_route", "quote_route", "webhook_route", "cli", "lookalike")))
    blocked = others - keys[entry] - keys["anchor"]
    return graph.path(keys[entry], keys["anchor"], dst_label=rf"^(?!.*({LOOKALIKE})).*{ANCHOR}",
                      max_hops=max_hops, blocked=blocked)


def test_invoice_issue_reaches_compute_vat_through_service(graph, keys):
    assert keys["invoice_service"], "InvoiceService missing"
    assert graph.path(keys["issue_route"], keys["invoice_service"], dst_label=INVOICE_SERVICE), \
        "POST /invoices -> InvoiceService missing"
    assert _reaches(graph, {**keys, "issue_route": keys["invoice_service"]}, "issue_route"), \
        "InvoiceService -> ... -> compute_vat missing"


def test_quote_route_reaches_compute_vat(graph, keys):
    assert _reaches(graph, keys, "quote_route", max_hops=2), "GET /quotes -> compute_vat missing"


def test_cli_job_reaches_compute_vat(graph, keys):
    """reissue-invoices is registered by @command in a module named only as a string in settings.JOB_MODULES."""
    assert _reaches(graph, keys, "cli"), "CLI reissue-invoices -> ... -> compute_vat missing"


def test_refund_webhook_reaches_compute_vat(graph, keys):
    """payment.refunded -> handle_refund (registered by @on) -> RefundService -> TAX_RULES['VAT'] -> compute_vat."""
    assert _reaches(graph, keys, "webhook_route"), "POST /webhooks/payments -> ... -> compute_vat missing"


def test_lookalike_report_vat_not_wired_to_billing_compute_vat(graph, keys):
    reached = graph.reachable(keys["lookalike"])
    assert not (reached & keys["anchor"]), (
        "GET /reports/vat drawn as reaching billing.tax.compute_vat; it calls reports.legacy_vat.compute_vat"
    )


def test_quote_route_repository_bypass_flagged_when_drawn(graph, keys):
    """The repository read is off the compute_vat path the user asked about, so drawing it is optional;
    if the diagram does show the route reaching PriceRepository directly, it must call that out."""
    edges = graph.adjacent(keys["quote_route"], keys["price_repo"]) if keys["price_repo"] else []
    if not edges:
        return
    flagged = any(re.search(VIOLATION, e.label, re.I) for e in edges) or any(
        re.search(VIOLATION, " ".join(graph.nodes[k].tags + [graph.nodes[k].label]), re.I)
        for k in keys["quote_route"]
    ) or any(
        re.search(rf"{QUOTE_ROUTE}|quote|PriceRepository", line, re.I) and re.search(VIOLATION, line, re.I)
        for line in DOC.read_text().splitlines()
    )
    assert flagged, "the quote route reading PriceRepository directly is not flagged as a layer violation"


@pytest.mark.parametrize(
    "role,pattern,layer",
    [("issue_route", ISSUE_ROUTE, "route"), ("quote_route", QUOTE_ROUTE, "route"), ("invoice_service", INVOICE_SERVICE, "service")],
)
def test_nodes_tagged_with_their_layer(graph, keys, role, pattern, layer):
    assert keys[role], f"no node for {role}"
    tagged = [
        k for k in keys[role]
        if re.search(LAYER_WORDS[layer], re.sub(PATHLIKE, " ", graph.layer_text(k, strip=pattern)), re.I)
    ]
    assert tagged, f"{role} node not tagged as {layer} layer (subgraph, class or label): " + str(
        [(graph.nodes[k].text, graph.nodes[k].tags) for k in keys[role]]
    )


def test_anchor_cited_with_file_and_line():
    lines = (BASE / "app/billing/tax.py").read_text().splitlines()
    start = next(i for i, ln in enumerate(lines, 1) if ln.startswith("def compute_vat"))
    end = start + 6
    cited = [int(n) for n in re.findall(r"tax\.py(?:\s*:\s*|#L|\s*,?\s*\(?(?:line|L)\s*)(\d+)", DOC.read_text(), re.I)]
    assert any(start - 1 <= n <= end for n in cited), f"compute_vat not cited as tax.py:<line> ({start}-{end}); found {cited}"


def test_application_code_untouched():
    diff = subprocess.run(
        ["diff", "-r", "-x", "__pycache__", "-x", "*.pyc", str(BASE / "app"), "/app/app"], capture_output=True, text=True
    )
    assert diff.returncode == 0, diff.stdout

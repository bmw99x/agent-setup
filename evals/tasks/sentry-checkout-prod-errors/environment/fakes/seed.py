"""Sentry state for checkout-api: a production regression since yesterday's 3.8.0 deploy, among decoys."""

from seedlib import D, H, ORG, PROJECTS, TOKEN, USER, events, frame, issue, write

API = "checkout/api.py"
ADDR = "{'country': 'GB', 'postcode': 'M1 1AE', 'region': 'ENG'}"
REQ = {"method": "POST", "url": "https://checkout.acme.test/orders"}

tax_frames = [
    frame(API, "create_order", "quote = quote_order(lines, address)", vars={"shipping": ADDR}),
    frame("checkout/pricing.py", "quote_order", "rate = vat_rate(address.country, address.region)",
          vars={"address": "Address(country='GB', postcode='M1 1AE', region='ENG')"}),
    frame("checkout/tax.py", "vat_rate", "return REGIONAL_RATES[(country, region)]",
          vars={"country": "'GB'", "region": "'ENG'"}),
]
gift_frames = [
    frame(API, "create_order", "total = promotions.apply_gift_card(total, payload[\"gift_card\"])",
          vars={"total": "Decimal('42.00')"}),
    frame("checkout/promotions.py", "apply_gift_card", "return max(total - card.balance",
          vars={"code": "'GC-50'", "card": "None"}),
]
pay_frames = [
    frame(API, "create_order", "charge_id = payments.charge(", rev="v3.7.2"),
    frame("checkout/payments.py", "charge", "with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS)"),
    frame("urllib/request.py", "urlopen", (215, "return opener.open(url, data, timeout)"), in_app=False),
    frame("ssl.py", "recv_into", (1251, "return self.read(nbytes, buffer)"), in_app=False),
]
db_frames = [
    frame(API, "create_order", "quote = quote_order(lines, address)"),
    frame("psycopg/connection.py", "connect", (119, "raise last_ex.with_traceback(None)"), in_app=False),
]
qty_frames = [frame(API, "parse_quantity", "return int(raw)", rev="v3.7.2", vars={"raw": "''"})]

checkout = [
    issue(6011873402, "CHECKOUT-API-3A", "checkout-api", "KeyError: ('GB', 'ENG')", "checkout.tax in vat_rate",
          count=1284, users=391, first=22 * H, last=240, priority="high", substatus="new",
          releases={"checkout-api@3.8.0": 1284},
          evs=events("CHECKOUT-API-3A", tax_frames, "KeyError", "('GB', 'ENG')", env="production",
                     release="checkout-api@3.8.0", first=22 * H, last=240, n=8, request=REQ,
                     tags={"transaction": "POST /orders", "server_name": "checkout-api-7d9f8"})),
    issue(5872210044, "CHECKOUT-API-1Z", "checkout-api", "TimeoutError: The read operation timed out",
          "checkout.payments in charge", count=8912, users=2210, first=41 * D, last=120,
          releases={"checkout-api@3.7.2": 8100, "checkout-api@3.8.0": 812},
          evs=events("CHECKOUT-API-1Z", pay_frames, "TimeoutError", "The read operation timed out", env="production",
                     release=lambda k: "checkout-api@3.7.2" if k < 4 else "checkout-api@3.8.0",
                     first=41 * D, last=120, n=8, request=REQ, tags={"transaction": "POST /orders"})),
    issue(6012004718, "CHECKOUT-API-39", "checkout-api", "AttributeError: 'NoneType' object has no attribute 'balance'",
          "checkout.promotions in apply_gift_card", count=57, users=12, first=18 * H, last=55 * 60, substatus="new",
          envs={"staging": 57}, releases={"checkout-api@3.9.0-rc1": 57},
          evs=events("CHECKOUT-API-39", gift_frames, "AttributeError", "'NoneType' object has no attribute 'balance'",
                     env="staging", release="checkout-api@3.9.0-rc1", first=18 * H, last=55 * 60, n=5, request=REQ)),
    issue(6011869930, "CHECKOUT-API-3B", "checkout-api",
          'OperationalError: connection to server at "orders-db" (10.4.0.12), port 5432 failed: Connection refused',
          "checkout.api in create_order", count=6, users=6, first=22 * H + 600, last=22 * H + 420, substatus="new",
          releases={"checkout-api@3.8.0": 6},
          evs=events("CHECKOUT-API-3B", db_frames, "OperationalError",
                     'connection to server at "orders-db" (10.4.0.12), port 5432 failed: Connection refused',
                     env="production", release="checkout-api@3.8.0", first=22 * H + 600, last=22 * H + 420, n=3)),
    issue(5790012388, "CHECKOUT-API-2Q", "checkout-api", "ValueError: invalid literal for int() with base 10: ''",
          "checkout.api in parse_quantity", count=342, users=120, first=60 * D, last=10 * D, status="resolved",
          releases={"checkout-api@3.7.1": 342},
          evs=events("CHECKOUT-API-2Q", qty_frames, "ValueError", "invalid literal for int() with base 10: ''",
                     env="production", release="checkout-api@3.7.1", first=60 * D, last=10 * D, n=4)),
]
web_frames = [frame("app/checkout/summary.tsx", "OrderSummary", (48, "const total = quote.total.toFixed(2);"),
                    in_app=False)]
storefront = [
    issue(6011880017, "STOREFRONT-WEB-7", "storefront-web",
          "TypeError: Cannot read properties of undefined (reading 'total')", "OrderSummary(app/checkout/summary)",
          count=2406, users=402, first=21 * H, last=300, priority="high", substatus="new",
          releases={"storefront-web@2026.11.3": 2406},
          evs=events("STOREFRONT-WEB-7", web_frames, "TypeError", "Cannot read properties of undefined (reading 'total')",
                     env="production", release="storefront-web@2026.11.3", first=21 * H, last=300, n=4)),
    issue(5660032001, "STOREFRONT-WEB-2", "storefront-web", "ChunkLoadError: Loading chunk 812 failed.",
          "app/layout", count=780, users=530, first=80 * D, last=3 * H, level="warning",
          evs=events("STOREFRONT-WEB-2", web_frames, "ChunkLoadError", "Loading chunk 812 failed.",
                     env="production", release="storefront-web@2026.11.3", first=80 * D, last=3 * H, n=3)),
]

releases = [
    {"org": "acme", "version": "checkout-api@3.7.2", "projects": ["checkout-api"], "ago": 41 * D,
     "deploys": [{"environment": "production", "ago": 41 * D}]},
    {"org": "acme", "version": "checkout-api@3.8.0", "projects": ["checkout-api"], "ago": 23 * H, "newGroups": 2,
     "deploys": [{"environment": "production", "ago": 22 * H + 900}]},
    {"org": "acme", "version": "checkout-api@3.9.0-rc1", "projects": ["checkout-api"], "ago": 19 * H, "newGroups": 1,
     "deploys": [{"environment": "staging", "ago": 18 * H + 1800}]},
    {"org": "acme", "version": "storefront-web@2026.11.3", "projects": ["storefront-web"], "ago": 3 * D,
     "deploys": [{"environment": "production", "ago": 3 * D}]},
]

write({"orgs": [ORG], "user": USER, "token": TOKEN, "projects": PROJECTS, "issues": checkout + storefront,
       "releases": releases})

"""Sentry state for the triage task: payments-api has more unresolved issues than one default page, and the
noisiest one is neither the most recent, the lexically largest count, nor the one affecting most users."""

from seedlib import D, H, ORG, PROJECTS, TOKEN, USER, events, frame, issue, write


def frames(module, function, line_no, line):
    return [frame("payments/api.py", "dispatch", (88, "return handler(request)")),
            frame(f"payments/{module}.py", function, (line_no, line))]


def pay(id, sid, title, culprit, count, users, first, last, status="unresolved", **kw):
    exc, _, value = title.partition(": ")
    module, function = culprit.removeprefix("payments.").split(" in ")
    fr = frames(module.replace(".", "/"), function, 40 + int(id) % 160, f"raise {exc}(...)")
    return issue(id, f"PAYMENTS-API-{sid}", "payments-api", title, culprit, count=count, users=users, first=first,
                 last=last, status=status, releases={"payments-api@2.14.0": count},
                 evs=events(f"PAYMENTS-API-{sid}", fr, exc, value, env="production", release="payments-api@2.14.0",
                            first=first, last=last, n=4), **kw)


FILLER = [
    ("CardDeclinedError: card_declined (insufficient_funds)", "payments.gateway in authorize", 2980, 2210),
    ("GatewayError: 502 Bad Gateway from acquirer", "payments.gateway in capture", 1714, 903),
    ("ValidationError: currency 'GBX' is not supported", "payments.money in parse_currency", 66, 41),
    ("WebhookSignatureError: signature mismatch", "payments.webhooks in verify_signature", 1220, 3),
    ("TimeoutError: bank-transfer API did not respond within 10s", "payments.bank in initiate_transfer", 845, 610),
    ("IntegrityError: duplicate key value violates unique constraint \"payments_idempotency_key\"",
     "payments.store in save_payment", 433, 377),
    ("KeyError: 'last4'", "payments.cards in mask_card", 291, 288),
    ("RefundAmountError: refund exceeds captured amount", "payments.refunds in validate_amount", 158, 97),
    ("ConnectionResetError: [Errno 104] Connection reset by peer", "payments.gateway in authorize", 1502, 1180),
    ("ThreeDSError: challenge expired", "payments.threeds in complete_challenge", 2207, 1950),
    ("RateLimitError: acquirer rate limit exceeded (429)", "payments.gateway in capture", 512, 12),
    ("DecimalException: [<class 'decimal.InvalidOperation'>]", "payments.money in to_minor_units", 38, 30),
    ("PayoutError: payout account not verified", "payments.payouts in schedule_payout", 77, 9),
    ("FraudCheckError: risk service unavailable", "payments.fraud in score", 1890, 1402),
    ("SerializationError: could not serialize access due to concurrent update", "payments.store in update_status",
     260, 201),
    ("AttributeError: 'NoneType' object has no attribute 'customer_id'", "payments.customers in get_or_create",
     149, 140),
    ("CurrencyMismatchError: refund currency EUR != charge currency GBP", "payments.refunds in issue_refund", 23, 21),
    ("DisputeSyncError: dispute dp_9xY2 not found at acquirer", "payments.disputes in sync", 312, 2),
    ("SettlementFileError: unexpected column 'fee_vat'", "payments.settlement in parse_file", 18, 1),
    ("ValueError: invalid IBAN checksum", "payments.bank in validate_iban", 702, 655),
    ("TokenizationError: vault returned 503", "payments.vault in tokenize", 1333, 1001),
    ("GatewayError: acquirer returned unknown response code 'Z9'", "payments.gateway in authorize", 401, 380),
    ("ApplePayError: merchant validation failed", "payments.wallets in validate_merchant", 2603, 2581),
    ("InvoiceError: VAT number missing for B2B invoice", "payments.invoices in render", 64, 60),
    ("LockTimeout: could not acquire payment lock within 5s", "payments.locks in acquire", 1175, 990),
    ("PermissionError: [Errno 13] Permission denied: '/var/run/payments/keys'", "payments.vault in load_keys", 12, 1),
    ("ChargebackError: evidence upload rejected (file too large)", "payments.disputes in upload_evidence", 9, 4),
    ("KeyError: 'BRL'", "payments.money in minor_unit_exponent", 120, 118),
    ("ReconciliationError: 3 payouts unmatched for 2026-11-11", "payments.settlement in reconcile", 31, 1),
    ("GooglePayError: unsupported auth method CRYPTOGRAM_3DS", "payments.wallets in decrypt_token", 1876, 1700),
    ("TypeError: unsupported operand type(s) for -: 'NoneType' and 'Decimal'", "payments.fees in net_amount",
     2770, 2112),
    ("SubscriptionError: renewal attempted on cancelled plan", "payments.subscriptions in renew", 588, 500),
    ("JSONDecodeError: Expecting value: line 1 column 1 (char 0)", "payments.gateway in parse_response", 2321, 1888),
    ("SSLError: certificate verify failed: certificate has expired", "payments.bank in initiate_transfer", 47, 40),
]

B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def sid(n):
    return (B36[n // 36] if n >= 36 else "") + B36[n % 36]


payments = []
used = {29, 48, 8, 92}  # T, 1C, 8, 2K
fill_ids = [n for n in range(40, 140) if n not in used][: len(FILLER)]
for k, ((title, culprit, count, users), n) in enumerate(zip(FILLER, fill_ids)):
    last = 600 + k * 1900          # 10 minutes .. ~17.6 hours ago, all more recent than the top issue
    payments.append(pay(5900000000 + n * 7, sid(n), title, culprit, count, users, first=(5 + k % 50) * D, last=last))

payments += [
    pay(5712004429, "T", "CardholderNameError: name contains unsupported characters",
        "payments.cards in normalise_cardholder", 10412, 1873, first=50 * D, last=20 * H),
    pay(5899003318, "1C", "PSD2ExemptionError: low-value exemption limit exceeded",
        "payments.threeds in request_exemption", 9877, 4120, first=12 * D, last=3600),
    pay(5501000877, "8", "OperationalError: server closed the connection unexpectedly",
        "payments.store in save_payment", 48210, 3900, first=88 * D, last=12 * D, status="resolved"),
    pay(5888120044, "2K", "HealthcheckWarning: acquirer sandbox unreachable",
        "payments.health in ping_acquirer", 15003, 1, first=70 * D, last=1800, status="ignored"),
]

web_frames = [frame("app/checkout/summary.tsx", "OrderSummary", (7, "<dd>{quote.total}</dd>"))]
storefront = [
    issue(6011880017, "STOREFRONT-WEB-7", "storefront-web",
          "TypeError: Cannot read properties of undefined (reading 'total')", "OrderSummary(app/checkout/summary)",
          count=25000, users=6120, first=9 * D, last=300, priority="high",
          evs=events("STOREFRONT-WEB-7", web_frames, "TypeError", "Cannot read properties of undefined (reading 'total')",
                     env="production", release="storefront-web@2026.11.3", first=9 * D, last=300, n=4)),
    issue(5660032001, "STOREFRONT-WEB-2", "storefront-web", "ChunkLoadError: Loading chunk 812 failed.",
          "app/layout", count=780, users=530, first=80 * D, last=3 * H, level="warning",
          evs=events("STOREFRONT-WEB-2", web_frames, "ChunkLoadError", "Loading chunk 812 failed.",
                     env="production", release="storefront-web@2026.11.3", first=80 * D, last=3 * H, n=3)),
]
checkout = [
    issue(5872210044, "CHECKOUT-API-1Z", "checkout-api", "TimeoutError: The read operation timed out",
          "checkout.payments in charge", count=18912, users=5210, first=41 * D, last=120,
          evs=events("CHECKOUT-API-1Z", [frame("checkout/payments.py", "charge", (14, "with urllib.request.urlopen("
                     "request, timeout=TIMEOUT_SECONDS) as response:"))], "TimeoutError", "The read operation timed out",
                     env="production", release="checkout-api@3.8.0", first=41 * D, last=120, n=4)),
]
releases = [
    {"org": "acme", "version": "payments-api@2.14.0", "projects": ["payments-api"], "ago": 6 * D,
     "deploys": [{"environment": "production", "ago": 6 * D}]},
    {"org": "acme", "version": "storefront-web@2026.11.3", "projects": ["storefront-web"], "ago": 3 * D,
     "deploys": [{"environment": "production", "ago": 3 * D}]},
]

write({"orgs": [ORG], "user": USER, "token": TOKEN, "projects": PROJECTS,
       "issues": storefront + payments + checkout, "releases": releases})

"""Sentry state for payments-api: the double-refund issue (fixed in 2.14.1, still firing from draining 2.14.0
workers) next to other refund/webhook issues that are not fixed."""

from seedlib import D, H, ORG, PROJECTS, TOKEN, USER, events, frame, issue, write

OLD = "v2.14.0"
refund_frames = [
    frame("payments/webhooks.py", "handle_refund_requested", "return issue_refund(gateway, charge,", rev=OLD,
          vars={"event": "{'charge_id': 'ch_3PqK2fLb', 'amount': '64.90', 'delivery_attempt': 2}"}),
    frame("payments/refunds.py", "issue_refund", "charge.refund_id = gateway.create_refund(charge.id, amount)", rev=OLD,
          vars={"charge": "Charge(id='ch_3PqK2fLb', captured=Decimal('64.90'), refund_id=None)"}),
    frame("payments/gateway.py", "create_refund", "raise GatewayError(", rev=OLD, vars={"charge_id": "'ch_3PqK2fLb'"}),
]
amount_frames = [
    frame("payments/webhooks.py", "handle_refund_requested", "return issue_refund(gateway, charge,", rev=OLD),
    frame("payments/refunds.py", "issue_refund", "validate_amount(charge, amount)", rev=OLD),
    frame("payments/refunds.py", "validate_amount", "raise RefundAmountError(", rev=OLD,
          vars={"amount": "Decimal('120.00')"}),
]
sig_frames = [frame("payments/webhooks.py", "verify_signature", "raise WebhookSignatureError(", rev=OLD)]
bank_frames = [frame("payments/bank.py", "initiate_transfer", (61, "response = self._session.post(url, json=body, timeout=10)"))]

old_release = {"payments-api@2.14.0": 1}

payments = [
    issue(6008812731, "PAYMENTS-API-3K", "payments-api", "GatewayError: charge ch_3PqK2fLb has already been refunded",
          "payments.gateway in create_refund", count=342, users=298, first=6 * D - 3 * H, last=40 * 60,
          priority="high", releases={"payments-api@2.14.0": 342}, value="charge ch_3PqK2fLb has already been refunded",
          evs=events("PAYMENTS-API-3K", refund_frames, "GatewayError", "charge ch_3PqK2fLb has already been refunded",
                     env="production", release="payments-api@2.14.0", first=6 * D - 3 * H, last=40 * 60, n=8,
                     tags={"transaction": "webhooks.charge.refund_requested", "worker": "refunds-batch"})),
    issue(6008830066, "PAYMENTS-API-3P", "payments-api", "RefundAmountError: refund of 120.00 exceeds captured amount 100.00",
          "payments.refunds in validate_amount", count=41, users=39, first=5 * D, last=2 * H,
          releases={"payments-api@2.14.0": 38, "payments-api@2.14.1": 3},
          evs=events("PAYMENTS-API-3P", amount_frames, "RefundAmountError",
                     "refund of 120.00 exceeds captured amount 100.00", env="production",
                     release=lambda k: "payments-api@2.14.1" if k == 4 else "payments-api@2.14.0",
                     first=5 * D, last=2 * H, n=5)),
    issue(5992210418, "PAYMENTS-API-41", "payments-api", "WebhookSignatureError: signature mismatch",
          "payments.webhooks in verify_signature", count=1220, users=3, first=30 * D, last=25 * 60,
          releases={"payments-api@2.14.0": 1100, "payments-api@2.14.1": 120},
          evs=events("PAYMENTS-API-41", sig_frames, "WebhookSignatureError", "signature mismatch", env="production",
                     release=lambda k: "payments-api@2.14.1" if k > 3 else "payments-api@2.14.0",
                     first=30 * D, last=25 * 60, n=6)),
    issue(5970045512, "PAYMENTS-API-2X", "payments-api", "TimeoutError: bank-transfer API did not respond within 10s",
          "payments.bank in initiate_transfer", count=845, users=610, first=45 * D, last=3 * H,
          evs=events("PAYMENTS-API-2X", bank_frames, "TimeoutError", "bank-transfer API did not respond within 10s",
                     env="production", release="payments-api@2.14.1", first=45 * D, last=3 * H, n=4)),
    issue(5801200987, "PAYMENTS-API-1M", "payments-api", "GatewayError: 502 Bad Gateway from acquirer",
          "payments.gateway in create_refund", count=96, users=90, first=70 * D, last=21 * D, status="resolved",
          evs=events("PAYMENTS-API-1M", bank_frames, "GatewayError", "502 Bad Gateway from acquirer",
                     env="production", release="payments-api@2.13.2", first=70 * D, last=21 * D, n=3)),
]
checkout = [
    issue(5872210044, "CHECKOUT-API-1Z", "checkout-api", "TimeoutError: The read operation timed out",
          "checkout.payments in charge", count=8912, users=2210, first=41 * D, last=120,
          evs=events("CHECKOUT-API-1Z", [frame("checkout/payments.py", "charge", (14, "with urllib.request.urlopen("
                     "request, timeout=TIMEOUT_SECONDS) as response:"))], "TimeoutError", "The read operation timed out",
                     env="production", release="checkout-api@3.8.0", first=41 * D, last=120, n=4)),
]
releases = [
    {"org": "acme", "version": "payments-api@2.13.2", "projects": ["payments-api"], "ago": 20 * D,
     "deploys": [{"environment": "production", "ago": 20 * D}]},
    {"org": "acme", "version": "payments-api@2.14.0", "projects": ["payments-api"], "ago": 6 * D, "newGroups": 2,
     "deploys": [{"environment": "staging", "ago": 6 * D + 2 * H}, {"environment": "production", "ago": 6 * D}]},
    {"org": "acme", "version": "payments-api@2.14.1", "projects": ["payments-api"], "ago": 4 * H, "commitCount": 2,
     "deploys": [{"environment": "staging", "ago": 4 * H}, {"environment": "production", "ago": 3 * H + 1800}]},
    {"org": "acme", "version": "checkout-api@3.8.0", "projects": ["checkout-api"], "ago": 23 * H,
     "deploys": [{"environment": "production", "ago": 22 * H}]},
]

write({"orgs": [ORG], "user": USER, "token": TOKEN, "projects": PROJECTS, "issues": payments + checkout,
       "releases": releases})

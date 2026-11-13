# History of shop/fulfilment: direct commits plus merged MRs (with review notes) and one
# open draft MR by the lead maintainer that only the forge holds.
# Commit, MR and Note are injected by build_history.py.

REPO = "shop/fulfilment"
HOST = "gitlab.example.test"
KIND = "gitlab"
PEOPLE = {
    "priya": ("Priya Shah", "priya@example.test"),
    "tom": ("Tom Reed", "tom@example.test"),
    "ana": ("Ana Costa", "ana@example.test"),
}

README = """# fulfilment

Warehouse fulfilment for the shop: turns paid orders into consignments, builds pick lists for
the warehouse floor, allocates a bay and despatches each consignment with a carrier.

## Running

    python -m pytest -q

## Layout

- `fulfilment/` — domain modules (consignments, pick lists, despatch)
- `fulfilment/gateways/` — the carrier API, the consignment store, the label printer
- `tests/` — pytest suite; `tests/fakes.py` holds in-memory gateways

Maintainer: Priya Shah (@priya).
"""

PYPROJECT = """[project]
name = "fulfilment"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

ERRORS_V1 = '''"""Errors the fulfilment domain raises. Every failure is a FulfilmentError."""


class FulfilmentError(Exception):
    """Base class for every fulfilment failure."""


class ConsignmentNotFound(FulfilmentError):
    """No consignment with that reference."""
'''

LEGACY_SHIPMENTS = '''"""Weight bands for parcels (pre-dates consignments)."""

from dataclasses import dataclass

WEIGHT_BANDS_GRAMS = (1000, 2000, 5000, 10000)


@dataclass(frozen=True)
class Shipment:
    reference: str
    weight_grams: int


def weight_band(shipment: Shipment) -> int:
    """The smallest band the shipment fits in, in grams."""
    for band in WEIGHT_BANDS_GRAMS:
        if shipment.weight_grams <= band:
            return band
    return WEIGHT_BANDS_GRAMS[-1]
'''

CONSIGNMENTS_DRAFT = '''"""Consignments: what leaves the warehouse in one parcel."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Bay:
    code: str
    capacity: int
    used: int


@dataclass(frozen=True)
class Consignment:
    reference: str
    weight_grams: int
    postage: float


def postage_for(weight_grams: int) -> float:
    return 3.45 if weight_grams <= 2000 else 6.10


def allocate_bay(consignment: Consignment, bays: list[Bay]) -> Bay | None:
    for bay in bays:
        if bay.used < bay.capacity:
            return bay
    return None
'''

CONSIGNMENTS = '''"""Consignments: what leaves the warehouse in one parcel."""

from dataclasses import dataclass

from fulfilment.errors import BayFull

SMALL_PARCEL_GRAMS = 2000
SMALL_PARCEL_POSTAGE_PENCE = 345
LARGE_PARCEL_POSTAGE_PENCE = 610


@dataclass(frozen=True)
class Bay:
    code: str
    capacity: int
    used: int


@dataclass(frozen=True)
class Consignment:
    reference: str
    weight_grams: int
    postage_pence: int


def postage_for(weight_grams: int) -> int:
    """Postage in pence for a parcel of this weight."""
    return SMALL_PARCEL_POSTAGE_PENCE if weight_grams <= SMALL_PARCEL_GRAMS else LARGE_PARCEL_POSTAGE_PENCE


def allocate_bay(consignment: Consignment, bays: list[Bay]) -> Bay:
    """The first bay with room for the consignment."""
    for bay in bays:
        if bay.used < bay.capacity:
            return bay
    raise BayFull(f"no bay has room for consignment {consignment.reference}")
'''

ERRORS_V2 = ERRORS_V1 + '''

class BayFull(FulfilmentError):
    """Every bay is at capacity."""
'''

FAKES_V1 = '''"""In-memory gateways for tests. Pass these in; do not patch modules."""

from fulfilment.consignments import Consignment
from fulfilment.errors import ConsignmentNotFound


class FakeConsignmentStore:
    def __init__(self, consignments: list[Consignment] = ()):
        self.consignments = {c.reference: c for c in consignments}
        self.despatched: list[str] = []

    def load(self, reference: str) -> Consignment:
        try:
            return self.consignments[reference]
        except KeyError:
            raise ConsignmentNotFound(reference) from None

    def mark_despatched(self, reference: str, tracking_number: str) -> None:
        self.despatched.append(reference)
'''

TEST_CONSIGNMENTS = '''import pytest

from fulfilment.consignments import Bay, Consignment, allocate_bay, postage_for
from fulfilment.errors import BayFull


def test_small_parcel_postage_is_345_pence():
    assert postage_for(1500) == 345


def test_large_parcel_postage_is_610_pence():
    assert postage_for(2500) == 610


def test_allocate_bay_picks_first_bay_with_room():
    bays = [Bay("A1", 2, 2), Bay("A2", 2, 1)]
    assert allocate_bay(Consignment("C-1", 900, 345), bays).code == "A2"


def test_allocate_bay_raises_when_every_bay_is_full():
    with pytest.raises(BayFull):
        allocate_bay(Consignment("C-1", 900, 345), [Bay("A1", 1, 1)])
'''

PICK_LISTS_DRAFT = '''"""Pick lists: what a picker collects from the shelves for one consignment."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PickLine:
    sku: str
    quantity: int
    location: str


@dataclass(frozen=True)
class PickList:
    shipment_ref: str
    lines: tuple[PickLine, ...]


def build_pick_list(shipment_ref: str, order_lines: list[tuple[str, int]], locations: dict[str, str]) -> PickList:
    lines = tuple(PickLine(sku, qty, locations[sku]) for sku, qty in sorted(order_lines, key=lambda l: locations[l[0]]))
    return PickList(shipment_ref, lines)
'''

PICK_LISTS = '''"""Pick lists: what a picker collects from the shelves for one consignment."""

from dataclasses import dataclass

from fulfilment.errors import FulfilmentError


class UnknownLocation(FulfilmentError):
    """A SKU on the order has no shelf location."""


@dataclass(frozen=True)
class PickLine:
    sku: str
    quantity: int
    location: str


@dataclass(frozen=True)
class PickList:
    consignment_ref: str
    lines: tuple[PickLine, ...]


def build_pick_list(consignment_ref: str, order_lines: list[tuple[str, int]], locations: dict[str, str]) -> PickList:
    """Pick lines in walking order (by shelf location)."""
    missing = [sku for sku, _ in order_lines if sku not in locations]
    if missing:
        raise UnknownLocation(f"no shelf location for {', '.join(missing)}")
    ordered = sorted(order_lines, key=lambda line: locations[line[0]])
    return PickList(consignment_ref, tuple(PickLine(sku, qty, locations[sku]) for sku, qty in ordered))
'''

TEST_PICK_LISTS_DRAFT = '''from unittest import mock

from fulfilment import pick_lists


def test_lines_follow_walking_order():
    with mock.patch.object(pick_lists, "PickList", wraps=pick_lists.PickList):
        pl = pick_lists.build_pick_list("S-1", [("B", 1), ("A", 2)], {"A": "01-02", "B": "01-01"})
    assert [l.sku for l in pl.lines] == ["B", "A"]
'''

TEST_PICK_LISTS = '''import pytest

from fulfilment.pick_lists import UnknownLocation, build_pick_list


def test_lines_follow_walking_order():
    pick_list = build_pick_list("C-1", [("B", 1), ("A", 2)], {"A": "01-02", "B": "01-01"})
    assert [line.sku for line in pick_list.lines] == ["B", "A"]


def test_unknown_location_raises():
    with pytest.raises(UnknownLocation):
        build_pick_list("C-1", [("Z", 1)], {})
'''

CARRIER_GATEWAY = '''"""The carrier's booking API. All HTTP to the carrier lives here."""

import json
import urllib.request

from fulfilment.errors import FulfilmentError

CARRIER_URL = "https://api.carrier.example.test/v1/collections"


class CarrierRejected(FulfilmentError):
    """The carrier refused to book the collection."""


def book_collection(consignment_ref: str, weight_grams: int) -> str:
    """Book a collection; returns the carrier's tracking number."""
    payload = json.dumps({"reference": consignment_ref, "weight_grams": weight_grams}).encode()
    request = urllib.request.Request(CARRIER_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.load(response)
    if body.get("status") != "booked":
        raise CarrierRejected(f"carrier refused {consignment_ref}: {body.get('reason', 'no reason given')}")
    return body["tracking_number"]
'''

CONSIGNMENT_STORE = '''"""The consignment store (SQLite). All database access lives here."""

import sqlite3

from fulfilment.consignments import Consignment
from fulfilment.errors import ConsignmentNotFound

DB_PATH = "fulfilment.db"


def load(reference: str) -> Consignment:
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute(
            "SELECT reference, weight_grams, postage_pence FROM consignments WHERE reference = ?", (reference,)
        ).fetchone()
    if row is None:
        raise ConsignmentNotFound(reference)
    return Consignment(*row)


def mark_despatched(reference: str, tracking_number: str) -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute("UPDATE consignments SET tracking_number = ? WHERE reference = ?", (tracking_number, reference))
'''

DESPATCH = '''"""Despatch: hand a consignment to the carrier.

Reads everything first, decides in pure functions, writes at the end.
"""

from dataclasses import dataclass

from fulfilment.consignments import Bay, allocate_bay


@dataclass(frozen=True)
class DespatchNote:
    consignment_ref: str
    bay: str
    tracking_number: str
    postage_pence: int


def despatch(consignment_ref: str, bays: list[Bay], *, store, carrier) -> DespatchNote:
    consignment = store.load(consignment_ref)
    bay = allocate_bay(consignment, bays)
    tracking_number = carrier.book_collection(consignment.reference, consignment.weight_grams)
    store.mark_despatched(consignment.reference, tracking_number)
    return DespatchNote(consignment.reference, bay.code, tracking_number, consignment.postage_pence)
'''

FAKE_CARRIER = '''

class FakeCarrier:
    def __init__(self, tracking_number: str = "TRK-1", rejects: bool = False):
        self.tracking_number = tracking_number
        self.rejects = rejects
        self.booked: list[str] = []

    def book_collection(self, consignment_ref: str, weight_grams: int) -> str:
        from fulfilment.gateways.carrier_gateway import CarrierRejected

        if self.rejects:
            raise CarrierRejected(consignment_ref)
        self.booked.append(consignment_ref)
        return self.tracking_number
'''

TEST_DESPATCH = '''import pytest

from fulfilment.consignments import Bay, Consignment
from fulfilment.despatch import despatch
from fulfilment.errors import BayFull
from fulfilment.gateways.carrier_gateway import CarrierRejected
from tests.fakes import FakeCarrier, FakeConsignmentStore


def test_despatch_books_collection_and_marks_consignment():
    store = FakeConsignmentStore([Consignment("C-1", 900, 345)])
    carrier = FakeCarrier("TRK-9")
    note = despatch("C-1", [Bay("A1", 2, 0)], store=store, carrier=carrier)
    assert (note.tracking_number, note.bay, note.postage_pence) == ("TRK-9", "A1", 345)
    assert store.despatched == ["C-1"]


def test_despatch_with_full_bays_books_nothing():
    store = FakeConsignmentStore([Consignment("C-1", 900, 345)])
    carrier = FakeCarrier()
    with pytest.raises(BayFull):
        despatch("C-1", [Bay("A1", 1, 1)], store=store, carrier=carrier)
    assert carrier.booked == []


def test_rejected_collection_is_not_marked_despatched():
    store = FakeConsignmentStore([Consignment("C-1", 900, 345)])
    with pytest.raises(CarrierRejected):
        despatch("C-1", [Bay("A1", 2, 0)], store=store, carrier=FakeCarrier(rejects=True))
    assert store.despatched == []
'''

BASE_GATEWAY = '''"""Base class for gateways."""

from abc import ABC, abstractmethod


class BaseGateway(ABC):
    @abstractmethod
    def healthcheck(self) -> bool: ...

    @abstractmethod
    def close(self) -> None: ...
'''

LABEL_PRINTER = '''"""The warehouse label printer (raw TCP)."""

import socket

from fulfilment.gateways.base import BaseGateway

PRINTER_ADDRESS = ("label-printer.warehouse.example.test", 9100)


class LabelPrinterGateway(BaseGateway):
    def __init__(self):
        self._sock = socket.create_connection(PRINTER_ADDRESS, timeout=5)

    def healthcheck(self) -> bool:
        return self._sock.fileno() != -1

    def print_label(self, consignment_ref: str, tracking_number: str) -> None:
        self._sock.sendall(f"^XA^FD{consignment_ref} {tracking_number}^FS^XZ".encode())

    def close(self) -> None:
        self._sock.close()
'''

STORE_INTERFACE_TEST = '''from tests.fakes import FakeConsignmentStore
from fulfilment.consignments import Consignment


def test_fake_store_records_despatch():
    store = FakeConsignmentStore([Consignment("C-1", 900, 345)])
    store.mark_despatched("C-1", "TRK-1")
    assert store.despatched == ["C-1"]
'''

DIRECTION_CARRIER = '''"""The carrier's booking API. All HTTP to the carrier lives here."""

import json
from typing import Protocol

from fulfilment.errors import FulfilmentError

CARRIER_URL = "https://api.carrier.example.test/v1/collections"


class CarrierRejected(FulfilmentError):
    """The carrier refused to book the collection."""


class HttpClient(Protocol):
    def post_json(self, url: str, payload: dict, *, timeout: float) -> dict: ...


class CarrierGateway:
    """Books collections with the carrier. Handed its HTTP client; never builds one."""

    def __init__(self, client: HttpClient):
        self._client = client

    def book_collection(self, consignment_ref: str, weight_grams: int) -> str:
        body = self._client.post_json(
            CARRIER_URL, {"reference": consignment_ref, "weight_grams": weight_grams}, timeout=10
        )
        if body.get("status") != "booked":
            raise CarrierRejected(f"carrier refused {consignment_ref}: {body.get('reason', 'no reason given')}")
        return body["tracking_number"]
'''

DIRECTION_STORE = '''"""The consignment store (SQLite). All database access lives here."""

import sqlite3

from fulfilment.consignments import Consignment
from fulfilment.errors import ConsignmentNotFound


class ConsignmentStore:
    """Loads and updates consignments. Handed its connection; never opens one."""

    def __init__(self, connection: sqlite3.Connection):
        self._db = connection

    def load(self, reference: str) -> Consignment:
        row = self._db.execute(
            "SELECT reference, weight_grams, postage_pence FROM consignments WHERE reference = ?", (reference,)
        ).fetchone()
        if row is None:
            raise ConsignmentNotFound(reference)
        return Consignment(*row)

    def mark_despatched(self, reference: str, tracking_number: str) -> None:
        self._db.execute("UPDATE consignments SET tracking_number = ? WHERE reference = ?", (tracking_number, reference))
'''

DIRECTION_TEST = '''import sqlite3

import pytest

from fulfilment.errors import ConsignmentNotFound
from fulfilment.gateways.carrier_gateway import CarrierGateway, CarrierRejected
from fulfilment.gateways.consignment_store import ConsignmentStore


class StubClient:
    def __init__(self, body):
        self.body = body

    def post_json(self, url, payload, *, timeout):
        return self.body


def test_carrier_gateway_returns_tracking_number():
    assert CarrierGateway(StubClient({"status": "booked", "tracking_number": "T"})).book_collection("C-1", 900) == "T"


def test_carrier_gateway_raises_when_rejected():
    with pytest.raises(CarrierRejected):
        CarrierGateway(StubClient({"status": "refused"})).book_collection("C-1", 900)


def test_store_raises_for_unknown_consignment():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE consignments (reference, weight_grams, postage_pence, tracking_number)")
    with pytest.raises(ConsignmentNotFound):
        ConsignmentStore(db).load("nope")
'''

STEPS = [
    Commit("priya", "2025-11-03T10:00:00+00:00", "chore: scaffold fulfilment service", {
        "README.md": README, "pyproject.toml": PYPROJECT, "CODEOWNERS": "* @priya\n",
        ".gitignore": "__pycache__/\n*.db\n.pytest_cache/\n",
        "fulfilment/__init__.py": "", "fulfilment/errors.py": ERRORS_V1, "tests/__init__.py": "",
    }),
    Commit("tom", "2025-11-20T15:12:00+00:00", "feat: parcel weight bands", {
        "fulfilment/legacy_shipments.py": LEGACY_SHIPMENTS,
    }),
    MR(4, "ana", "Consignments and postage", "Adds consignments, postage and bay allocation.",
       "feature/consignments", "2026-01-08T09:00:00+00:00",
       commits=[
           Commit("ana", "2026-01-08T09:00:00+00:00", "feat: consignments, postage and bays",
                  {"fulfilment/consignments.py": CONSIGNMENTS_DRAFT}),
           Commit("ana", "2026-01-13T11:20:00+00:00", "review: int pence, raise BayFull, tests",
                  {"fulfilment/consignments.py": CONSIGNMENTS, "fulfilment/errors.py": ERRORS_V2,
                   "tests/fakes.py": FAKES_V1, "tests/test_consignments.py": TEST_CONSIGNMENTS}),
       ],
       notes=[
           Note("priya", "2026-01-09T10:02:00+00:00",
                "Money is `int` pence everywhere in this service — please drop the float `postage` and use "
                "`postage_pence: int`. Floats round wrong on totals.", "fulfilment/consignments.py", 20),
           Note("priya", "2026-01-09T10:05:00+00:00",
                "Returning `None` when the bays are full hides the problem from the caller. Raise `BayFull` "
                "(a `FulfilmentError`) instead — we fail loud.", "fulfilment/consignments.py", 27),
           Note("ana", "2026-01-13T11:21:00+00:00", "Both done, plus tests."),
       ],
       merged_at="2026-01-15T16:40:00+00:00", merged_by="priya"),
    MR(9, "tom", "Pick lists", "Pick lists in walking order for the warehouse floor.",
       "feature/pick-lists", "2026-02-20T13:00:00+00:00",
       commits=[
           Commit("tom", "2026-02-20T13:00:00+00:00", "feat: pick lists",
                  {"fulfilment/pick_lists.py": PICK_LISTS_DRAFT, "tests/test_pick_lists.py": TEST_PICK_LISTS_DRAFT}),
           Commit("tom", "2026-02-27T10:10:00+00:00", "review: consignment naming, no mock.patch, unknown locations",
                  {"fulfilment/pick_lists.py": PICK_LISTS, "tests/test_pick_lists.py": TEST_PICK_LISTS}),
       ],
       notes=[
           Note("priya", "2026-02-23T09:30:00+00:00",
                "We call it a consignment — 'shipment' is the carrier's word, not ours. No new `shipment` names "
                "please (`shipment_ref` → `consignment_ref`); `legacy_shipments.py` gets folded in when someone next "
                "touches it.", "fulfilment/pick_lists.py", 15),
           Note("priya", "2026-02-23T09:34:00+00:00",
                "Please don't `mock.patch` our own modules in tests — build the real thing, and for gateways pass "
                "the in-memory fakes from `tests/fakes.py`.", "tests/test_pick_lists.py", 6),
           Note("priya", "2026-02-23T09:36:00+00:00",
                "An unknown SKU location should raise (a `FulfilmentError` subclass), not KeyError out of a lambda.",
                "fulfilment/pick_lists.py", 19),
       ],
       merged_at="2026-03-02T12:00:00+00:00", merged_by="priya"),
    MR(14, "ana", "Despatch via the carrier gateway", "Despatch books a carrier collection and records it.",
       "feature/despatch", "2026-04-28T08:45:00+00:00",
       commits=[
           Commit("ana", "2026-04-28T08:45:00+00:00", "feat: despatch consignments", {
               "fulfilment/gateways/__init__.py": "",
               "fulfilment/gateways/carrier_gateway.py": CARRIER_GATEWAY,
               "fulfilment/gateways/consignment_store.py": CONSIGNMENT_STORE,
               "fulfilment/despatch.py": DESPATCH,
               "tests/fakes.py": lambda old: old + FAKE_CARRIER,
               "tests/test_despatch.py": TEST_DESPATCH,
           }),
       ],
       notes=[
           Note("priya", "2026-04-30T14:10:00+00:00",
                "The first version had `urlopen` inside `consignments.py`. Thanks for moving it: HTTP and SQL live "
                "in `fulfilment/gateways/` only, the domain modules stay pure and never import a gateway."),
           Note("priya", "2026-04-30T14:12:00+00:00",
                "`despatch()` reads first (store), decides in the pure functions, then does its writes at the end "
                "(carrier, store). Keep it that way — no store calls between decisions.", "fulfilment/despatch.py", 20),
           Note("priya", "2026-04-30T14:15:00+00:00",
                "And the tests pass `FakeCarrier`/`FakeConsignmentStore` — exactly right, no patching.",
                "tests/test_despatch.py", 12),
       ],
       merged_at="2026-05-11T10:30:00+00:00", merged_by="priya"),
    MR(19, "tom", "Label printer gateway", "Prints despatch labels on the warehouse Zebra printer.",
       "feature/label-printer", "2026-06-30T16:00:00+00:00",
       commits=[
           Commit("tom", "2026-06-30T16:00:00+00:00", "feat: label printer gateway with a base gateway class", {
               "fulfilment/gateways/base.py": BASE_GATEWAY,
               "fulfilment/gateways/label_printer_gateway.py": LABEL_PRINTER,
           }),
       ],
       notes=[
           Note("priya", "2026-07-02T09:00:00+00:00",
                "No ABC base classes please. The other gateways are plain modules and the tests pass fakes, so "
                "`BaseGateway` buys us nothing but ceremony. Merging only to unblock the warehouse pilot — don't "
                "build on `BaseGateway`; it goes when the label printer is reworked.", "fulfilment/gateways/base.py", 6),
           Note("tom", "2026-07-02T09:20:00+00:00", "Understood — one-off, I'll not extend it."),
       ],
       merged_at="2026-07-08T11:00:00+00:00", merged_by="priya"),
    MR(23, "ana", "Fake store contract test", "Small test for the fake store's despatch record.",
       "test/fake-store", "2026-09-15T10:00:00+00:00",
       commits=[Commit("ana", "2026-09-15T10:00:00+00:00", "test: fake store records despatch",
                       {"tests/test_fakes.py": STORE_INTERFACE_TEST})],
       notes=[
           Note("priya", "2026-09-18T08:40:00+00:00",
                "Fine. Reminder for everyone: postage and prices stay `int` pence — I saw a `Decimal` creep into a "
                "branch last week. And failures raise a `FulfilmentError` subclass; never return `None` for 'it went wrong'."),
       ],
       merged_at="2026-09-21T09:00:00+00:00", merged_by="priya"),
    MR(31, "priya", "Draft: gateways take their client in the constructor",
       "Direction for gateways, not merged yet.\n\n"
       "Each gateway becomes a small class that is handed its client or connection in `__init__` "
       "(`CarrierGateway(client)`, `ConsignmentStore(connection)`) instead of building one from module "
       "globals. Tests construct the gateway with a stub client. New gateways should follow this shape "
       "once it lands; existing callers move over in this MR.",
       "priya/gateway-constructors", "2026-11-05T09:15:00+00:00",
       commits=[
           Commit("priya", "2026-11-05T09:15:00+00:00", "refactor: gateways are handed their client", {
               "fulfilment/gateways/carrier_gateway.py": DIRECTION_CARRIER,
               "fulfilment/gateways/consignment_store.py": DIRECTION_STORE,
               "tests/test_gateways.py": DIRECTION_TEST,
           }),
       ],
       draft=True),
]

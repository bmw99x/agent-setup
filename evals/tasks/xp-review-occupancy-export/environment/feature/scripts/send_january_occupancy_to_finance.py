"""One-off: finance asked for January 2026 before ROOMS-142 shipped. Run once, then delete."""

import sys

from app.reports.export import export_report
from app.reports.occupancy import build_occupancy_report
from app.rooms.repository import BookingRepository


def main(repository: BookingRepository) -> None:
    rows = build_occupancy_report(repository, 2026, 1)
    data, _ = export_report(rows)
    out = sys.argv[1] if len(sys.argv) > 1 else "occupancy-2026-01.csv"
    with open(out, "wb") as f:
        f.write(data)
    print("wrote", out, len(rows), "rooms")

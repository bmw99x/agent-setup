from ingest.models import Reading, Rejected

MAX_KWH_PER_READING = 500.0


def validate(readings: list[Reading]) -> tuple[list[Reading], list[Rejected]]:
    good, bad = [], []
    for reading in readings:
        if reading.kwh < 0 or reading.kwh > MAX_KWH_PER_READING:
            bad.append(Rejected(f"{reading.meter_id},{reading.taken_at.isoformat()}", f"kwh out of range: {reading.kwh}"))
        else:
            good.append(reading)
    return good, bad

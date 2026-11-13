import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BatchQueue:
    """Payout ids waiting for the next bank batch, one JSON line each in the spool file."""

    spool: Path

    def enqueue(self, payout_id: str) -> None:
        with self.spool.open("a") as fh:
            fh.write(json.dumps({"payout_id": payout_id}) + "\n")

    def drain(self) -> list[str]:
        if not self.spool.exists():
            return []
        ids = [json.loads(line)["payout_id"] for line in self.spool.read_text().splitlines() if line]
        self.spool.write_text("")
        return ids

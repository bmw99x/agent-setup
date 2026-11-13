import os
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class SftpSource:
    """Daily CSV drops from the meter vendor's SFTP server, copied down with the system `sftp` client."""

    host: str
    inbox: str
    download_dir: Path

    @classmethod
    def from_env(cls) -> "SftpSource":
        return cls(os.environ["VENDOR_SFTP_HOST"], "/outbound/readings", Path(os.environ["INGEST_DOWNLOAD_DIR"]))

    def fetch(self, day: date) -> list[Path]:
        target = self.download_dir / day.isoformat()
        target.mkdir(parents=True, exist_ok=True)
        batch = f"get {self.inbox}/{day:%Y%m%d}_*.csv {target}/\n"
        subprocess.run(["sftp", "-b", "-", self.host], input=batch, text=True, check=True)
        return sorted(target.glob("*.csv"))

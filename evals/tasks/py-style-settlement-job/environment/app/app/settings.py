import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    storage_account_url: str


def load_settings() -> Settings:
    return Settings(storage_account_url=os.environ["STORAGE_ACCOUNT_URL"])

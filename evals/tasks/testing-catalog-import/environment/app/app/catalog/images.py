"""Product images: download from the supplier and store in our bucket."""

from dataclasses import dataclass


class ImageUnavailableError(Exception):
    """The supplier's image could not be downloaded."""


@dataclass(frozen=True)
class StoredImage:
    key: str
    size_bytes: int


class SupplierImageStore:
    """Downloads each image over HTTP (slow, metered by the supplier) and uploads it to the bucket."""

    def fetch(self, url: str) -> StoredImage:
        raise ConnectionError(f"cannot download {url}: no network")

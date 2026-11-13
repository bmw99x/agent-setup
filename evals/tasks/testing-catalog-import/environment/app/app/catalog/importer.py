"""Import a supplier's product feed into the catalog."""

from collections.abc import Iterable
from dataclasses import dataclass, field

from app.catalog.images import ImageUnavailableError, SupplierImageStore
from app.catalog.models import Product
from app.catalog.repository import ProductRepository


@dataclass
class ImportReport:
    imported: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


def normalise_sku(raw: str) -> str:
    return raw.strip().upper()


class CatalogImporter:
    def __init__(self, repository: ProductRepository, images: SupplierImageStore) -> None:
        self._repository = repository
        self._images = images

    def import_rows(self, rows: Iterable[dict[str, str]]) -> ImportReport:
        """Add each feed row as a product.

        A SKU already in the catalog (including one added earlier in the same feed) is
        reported as a duplicate and skipped, and its image is not downloaded. A row whose
        image can't be downloaded is reported as failed and not added.
        """
        report = ImportReport()
        for row in rows:
            sku = normalise_sku(row["sku"])
            if self._repository.get(sku) is not None:
                report.duplicates.append(sku)
                continue
            try:
                image = self._images.fetch(row["image_url"])
            except ImageUnavailableError as error:
                report.failed[sku] = str(error)
                continue
            self._repository.add(
                Product(sku=sku, name=row["name"].strip(), price_pence=int(row["price_pence"]), image_key=image.key)
            )
            report.imported.append(sku)
        return report

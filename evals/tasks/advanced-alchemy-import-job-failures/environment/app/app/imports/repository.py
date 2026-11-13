from advanced_alchemy.extensions.fastapi import repository

from app.imports.models import ImportJob


class ImportJobRepository(repository.SQLAlchemyAsyncRepository[ImportJob]):
    model_type = ImportJob

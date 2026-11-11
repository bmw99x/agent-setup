---
name: pydantic
description: Use when creating, defining, or reviewing pydantic v2 schemas/DTOs — triggers on "add schema", "create DTO", "define request/response model", "add serializer". Covers project base model inheritance, Datum/Upsert naming suffixes, camelCase aliases, X | None typing, @field_validator/@model_validator rules, no ORM lazy-loads in validators, and pydantic-settings for config.
---

# pydantic.md

## Version

Pydantic v2. `pydantic[email]>=2.12.5`.

## Base model

All API schemas inherit from a single project base model (e.g. `AppBaseModel` in a shared validation/schemas module):

```python
from app.validation.schemas import AppBaseModel

class MyDatum(AppBaseModel):
    id: UUID
    name: str
    created_at: datetime = Field(..., alias="createdAt")
```

Do not inherit from `BaseModel` directly — use the project base model.

## Schema naming

| Purpose | Suffix | Example |
|---------|--------|---------|
| Read (GET response) | `Datum` | `ProductDatum` |
| Write (POST/PUT/PATCH body) | `Upsert` / `UpsertDatum` | `ProductUpsertDatum` |
| Bulk write | `UpsertMany` (dataclass) | `ProductUpsertMany` |
| Filtered read | descriptive | `DiscountedProductDatum` |

Bulk write payloads use `@dataclass`, not the project base model:

```python
from dataclasses import dataclass

@dataclass
class ProductUpsertMany:
    data: list[ProductUpsertDatum]
```

## Fields

- Aliases: camelCase externally (`alias="createdAt"`), snake internally
- `X | None` not `Optional[X]`
- No default values on required fields — use `Field(...)` or bare annotation
- Constraints inline: `Field(gt=0)`, `Field(max_length=255)`
- `populate_by_name=True` if both alias and field name need to work

## Validators

- `@field_validator` for single-field validation
- `@model_validator(mode="after")` for cross-field validation
- No side effects in validators — pure validation only
- Shared validators: module-level functions, imported where needed
- A field accepting several input shapes (an int or a list of ints folded to one mask): `Annotated[int | None, BeforeValidator(fold), AfterValidator(check)]`, not a custom class with `__get_pydantic_core_schema__`. Raise `PydanticCustomError` from validators so 422 responses serialise.

## Serialisation

- `model.model_dump(by_alias=True)` for external output
- `model.model_dump(mode="json")` for JSON-safe output
- `service.to_schema(data, schema_type=SchemaCls)` — use this in routes, not manual `.model_dump()`

## ORM integration

- `model_config = ConfigDict(from_attributes=True)` on read schemas (set once in the project base model)
- ORM → schema via `service.to_schema()` — never access ORM attributes directly in route
- Never trigger lazy loads from inside a pydantic validator

## Settings

- `pydantic-settings` `BaseSettings` for config classes (e.g. `app/config/settings.py`)
- `.env` loaded via `find_dotenv(".env")`
- Env vars as single source of config — no ad-hoc secrets hierarchy

## Forbidden

- Inheriting from `BaseModel` directly — use the project base model
- Side effects in validators (DB calls, HTTP calls)
- Mutating model in validator
- Accessing ORM relationships inside pydantic schema (lazy-load risk)
- `model_dump()` without `by_alias=True` when sending to client

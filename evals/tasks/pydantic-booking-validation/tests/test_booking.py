import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, "/app")
from app.bookings.schemas import BookingUpsertDatum  # noqa: E402

SOURCE = Path("/app/app/bookings/schemas.py").read_text()
BASE = {"roomId": 1, "startAt": "2026-01-01T09:00:00", "endAt": "2026-01-01T10:00:00"}


def _error_type(payload):
    with pytest.raises(ValidationError) as exc:
        BookingUpsertDatum.model_validate(payload)
    return exc.value.errors()[0]["type"]


@pytest.mark.parametrize(("weekdays", "mask"), [(5, 5), ([0, 2], 5), ([6], 64), ([], 0)])
def test_weekdays_folded(weekdays, mask):
    assert BookingUpsertDatum.model_validate({**BASE, "weekdays": weekdays}).weekdays == mask


@pytest.mark.parametrize("weekdays", [[7], [-1], 128])
def test_weekdays_out_of_range_rejected(weekdays):
    _error_type({**BASE, "weekdays": weekdays})


def test_end_before_start_rejected():
    _error_type({**BASE, "endAt": "2026-01-01T08:00:00"})


def test_rejections_use_custom_error_types():
    generic = {"value_error", "assertion_error", "greater_than_equal", "less_than_equal", "less_than", "greater_than"}
    weekday_type = _error_type({**BASE, "weekdays": [9]})
    range_type = _error_type({**BASE, "endAt": "2026-01-01T08:00:00"})
    assert weekday_type not in generic, "raise PydanticCustomError so 422s carry a custom type"
    assert range_type not in generic, "raise PydanticCustomError so 422s carry a custom type"
    assert weekday_type != range_type


def test_cross_field_check_is_after_model_validator():
    validators = BookingUpsertDatum.__pydantic_decorators__.model_validators
    assert any(v.info.mode == "after" for v in validators.values())


def test_multi_shape_field_uses_annotated_validators_not_custom_type():
    assert "__get_pydantic_core_schema__" not in SOURCE
    assert "BeforeValidator" in SOURCE and "Annotated" in SOURCE

import pytest
from pydantic import ValidationError


def test_health_payload_valid():
    from models import HealthPayload

    payload = HealthPayload(
        source="nutrition",
        data={
            "date": "2026-04-01",
            "calories": 2200,
            "protein_g": 160,
            "carbs_g": 200,
            "fat_g": 70,
        },
    )
    assert payload.source == "nutrition"
    assert payload.data.date == "2026-04-01"
    assert payload.data.calories == 2200
    assert payload.data.protein_g == 160
    assert payload.data.carbs_g == 200
    assert payload.data.fat_g == 70


def test_health_data_missing_field_raises():
    from models import HealthPayload

    with pytest.raises(ValidationError):
        HealthPayload(
            source="nutrition",
            data={"date": "2026-04-01", "calories": 2200},  # missing macros
        )


def test_health_payload_missing_data_raises():
    from models import HealthPayload

    with pytest.raises(ValidationError):
        HealthPayload(source="nutrition")


def test_health_data_invalid_date_type_raises():
    from models import HealthPayload

    with pytest.raises(ValidationError):
        HealthPayload(
            source="nutrition",
            data={
                "date": 20260401,  # int instead of str
                "calories": 2200,
                "protein_g": 160,
                "carbs_g": 200,
                "fat_g": 70,
            },
        )

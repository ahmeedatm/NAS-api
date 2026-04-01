import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport


VALID_PAYLOAD = {
    "source": "nutrition",
    "data": {
        "date": "2026-04-01",
        "calories": 2200,
        "protein_g": 160,
        "carbs_g": 200,
        "fat_g": 70,
    },
}


@pytest.mark.anyio
async def test_post_health_returns_200_on_valid_payload():
    from main import app

    with patch("main.find_or_create_week", return_value="week-abc"), \
         patch("main.create_day_entry", return_value="day-xyz"), \
         patch("main.update_week_averages"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["day_page_id"] == "day-xyz"


@pytest.mark.anyio
async def test_post_health_returns_422_on_missing_data_field():
    from main import app

    with patch("main.find_or_create_week", return_value="w"), \
         patch("main.create_day_entry", return_value="d"), \
         patch("main.update_week_averages"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/", json={"source": "nutrition"})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_post_health_returns_422_on_missing_calories():
    from main import app

    payload = {
        "source": "nutrition",
        "data": {"date": "2026-04-01", "protein_g": 160, "carbs_g": 200, "fat_g": 70},
    }
    with patch("main.find_or_create_week", return_value="w"), \
         patch("main.create_day_entry", return_value="d"), \
         patch("main.update_week_averages"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/", json=payload)

    assert response.status_code == 422


@pytest.mark.anyio
async def test_post_health_returns_500_on_notion_error():
    from main import app

    with patch("main.find_or_create_week", side_effect=Exception("Notion API error")), \
         patch("main.create_day_entry", return_value="d"), \
         patch("main.update_week_averages"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/", json=VALID_PAYLOAD)

    assert response.status_code == 500
    assert "error" in response.json()


@pytest.mark.anyio
async def test_post_health_calls_find_or_create_week():
    from main import app
    import datetime

    with patch("main.find_or_create_week", return_value="week-abc") as mock_week, \
         patch("main.create_day_entry", return_value="day-xyz"), \
         patch("main.update_week_averages"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/", json=VALID_PAYLOAD)

    mock_week.assert_called_once()
    assert mock_week.call_args[0][1] == datetime.date(2026, 4, 1)


@pytest.mark.anyio
async def test_post_health_calls_create_day_entry():
    from main import app

    with patch("main.find_or_create_week", return_value="week-abc"), \
         patch("main.create_day_entry", return_value="day-xyz") as mock_day, \
         patch("main.update_week_averages"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/", json=VALID_PAYLOAD)

    mock_day.assert_called_once()
    assert mock_day.call_args[0][2] == "week-abc"


@pytest.mark.anyio
async def test_post_health_calls_update_week_averages():
    from main import app

    with patch("main.find_or_create_week", return_value="week-abc"), \
         patch("main.create_day_entry", return_value="day-xyz"), \
         patch("main.update_week_averages") as mock_avg:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/", json=VALID_PAYLOAD)

    mock_avg.assert_called_once()
    assert mock_avg.call_args[0][1] == "week-abc"

import datetime
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# get_monday
# ---------------------------------------------------------------------------

def test_get_monday_returns_same_day_on_monday():
    from notion_service import get_monday
    assert get_monday(datetime.date(2026, 3, 30)) == datetime.date(2026, 3, 30)


def test_get_monday_returns_previous_monday_midweek():
    from notion_service import get_monday
    assert get_monday(datetime.date(2026, 4, 1)) == datetime.date(2026, 3, 30)  # Wednesday → Monday


def test_get_monday_returns_previous_monday_on_sunday():
    from notion_service import get_monday
    assert get_monday(datetime.date(2026, 4, 5)) == datetime.date(2026, 3, 30)  # Sunday → Monday


# ---------------------------------------------------------------------------
# find_week_by_date
# ---------------------------------------------------------------------------

def test_find_week_by_date_returns_page_id_when_found():
    from notion_service import find_week_by_date

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [{"id": "abc-123"}]}

    result = find_week_by_date(mock_client, datetime.date(2026, 3, 30), "db-weeks-id")

    assert result == "abc-123"
    call_kwargs = mock_client.data_sources.query.call_args[1]
    assert call_kwargs["filter"]["property"] == "Date"
    assert call_kwargs["filter"]["date"]["equals"] == "2026-03-30"


def test_find_week_by_date_returns_none_when_not_found():
    from notion_service import find_week_by_date

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": []}

    result = find_week_by_date(mock_client, datetime.date(2026, 3, 30), "db-weeks-id")

    assert result is None


# ---------------------------------------------------------------------------
# get_next_week_number
# ---------------------------------------------------------------------------

def _make_week_result(title: str) -> dict:
    return {"properties": {"Semaine": {"title": [{"plain_text": title}]}}}


def test_get_next_week_number_returns_1_when_no_weeks():
    from notion_service import get_next_week_number

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": []}

    assert get_next_week_number(mock_client, "db-weeks-id") == 1


def test_get_next_week_number_increments_max():
    from notion_service import get_next_week_number

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [
        _make_week_result("Semaine 1"),
        _make_week_result("Semaine 2"),
    ]}

    assert get_next_week_number(mock_client, "db-weeks-id") == 3


def test_get_next_week_number_handles_non_sequential_weeks():
    from notion_service import get_next_week_number

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [
        _make_week_result("Semaine 0"),
        _make_week_result("Semaine 3"),
    ]}

    assert get_next_week_number(mock_client, "db-weeks-id") == 4


# ---------------------------------------------------------------------------
# create_week_page
# ---------------------------------------------------------------------------

def test_create_week_page_returns_new_page_id():
    from notion_service import create_week_page

    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "new-week-999"}

    result = create_week_page(mock_client, 2, datetime.date(2026, 3, 30), "db-weeks-id")

    assert result == "new-week-999"


def test_create_week_page_sends_correct_title_and_date():
    from notion_service import create_week_page

    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "new-week-999"}

    create_week_page(mock_client, 2, datetime.date(2026, 3, 30), "db-weeks-id")

    props = mock_client.pages.create.call_args[1]["properties"]
    assert props["Semaine"]["title"][0]["text"]["content"] == "Semaine 2"
    assert props["Date"]["date"]["start"] == "2026-03-30"


# ---------------------------------------------------------------------------
# find_or_create_week
# ---------------------------------------------------------------------------

def test_find_or_create_week_returns_existing_week():
    from notion_service import find_or_create_week

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [{"id": "existing-week"}]}

    result = find_or_create_week(mock_client, datetime.date(2026, 4, 1), "db-weeks-id")

    assert result == "existing-week"
    mock_client.pages.create.assert_not_called()


def test_find_or_create_week_creates_with_incremented_number():
    from notion_service import find_or_create_week

    mock_client = MagicMock()
    # First call (find_week_by_date): not found
    # Second call (get_next_week_number): returns existing weeks
    mock_client.data_sources.query.side_effect = [
        {"results": []},  # find_week_by_date → not found
        {"results": [_make_week_result("Semaine 1")]},  # get_next_week_number → max=1
    ]
    mock_client.pages.create.return_value = {"id": "new-week"}

    result = find_or_create_week(mock_client, datetime.date(2026, 4, 6), "db-weeks-id")

    assert result == "new-week"
    props = mock_client.pages.create.call_args[1]["properties"]
    assert props["Semaine"]["title"][0]["text"]["content"] == "Semaine 2"
    assert props["Date"]["date"]["start"] == "2026-04-06"  # Monday


# ---------------------------------------------------------------------------
# get_activity_for_date
# ---------------------------------------------------------------------------

def _make_workout_result(sport: str) -> dict:
    return {"properties": {"Sport": {"select": {"name": sport}}}}


def test_get_activity_for_date_returns_repos_when_no_entry():
    from notion_service import get_activity_for_date

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": []}

    assert get_activity_for_date(mock_client, datetime.date(2026, 4, 1), "db-workout-id") == "Repos"


def test_get_activity_for_date_returns_kine():
    from notion_service import get_activity_for_date

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [_make_workout_result("Kiné")]}

    assert get_activity_for_date(mock_client, datetime.date(2026, 4, 1), "db-workout-id") == "Kiné"


@pytest.mark.parametrize("sport", ["Calisthénie", "Volley", "Mixte"])
def test_get_activity_for_date_returns_entrainement(sport):
    from notion_service import get_activity_for_date

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [_make_workout_result(sport)]}

    assert get_activity_for_date(mock_client, datetime.date(2026, 4, 1), "db-workout-id") == "Entrainement"


# ---------------------------------------------------------------------------
# create_day_entry
# ---------------------------------------------------------------------------

def test_create_day_entry_returns_page_id():
    from notion_service import create_day_entry
    from models import HealthData

    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "day-page-555"}

    data = HealthData(date="2026-04-01", calories=2200, protein_g=160, carbs_g=200, fat_g=70, weight_kg_x10=744)
    with patch("notion_service.get_activity_for_date", return_value="Repos"):
        result = create_day_entry(mock_client, data, "week-page-id", "db-days-id", "db-workout-id")

    assert result == "day-page-555"


def test_create_day_entry_sets_all_properties():
    from notion_service import create_day_entry
    from models import HealthData

    mock_client = MagicMock()
    mock_client.pages.create.return_value = {"id": "day-page-555"}

    data = HealthData(date="2026-04-01", calories=2200, protein_g=160, carbs_g=200, fat_g=70, weight_kg_x10=744)
    with patch("notion_service.get_activity_for_date", return_value="Entrainement"):
        create_day_entry(mock_client, data, "week-page-id", "db-days-id", "db-workout-id")

    props = mock_client.pages.create.call_args[1]["properties"]
    assert props["Calories"]["number"] == 2200
    assert props["Proteins"]["number"] == 160
    assert props["Carbs"]["number"] == 200
    assert props["Fats"]["number"] == 70
    assert props["Poids"]["number"] == 74.4
    assert props["Activité"]["select"]["name"] == "Entrainement"
    assert props["Date"]["date"]["start"] == "2026-04-01"
    assert props["Week"]["relation"][0]["id"] == "week-page-id"


# ---------------------------------------------------------------------------
# update_week_averages
# ---------------------------------------------------------------------------

def test_update_week_averages_computes_correct_means():
    from notion_service import update_week_averages

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {
        "results": [
            {"properties": {"Calories": {"number": 2100}, "Proteins": {"number": 150}, "Carbs": {"number": 200}, "Fats": {"number": 60}, "Poids": {"number": 74.0}}},
            {"properties": {"Calories": {"number": 2300}, "Proteins": {"number": 170}, "Carbs": {"number": 220}, "Fats": {"number": 80}, "Poids": {"number": 74.8}}},
        ]
    }

    update_week_averages(mock_client, "week-id", "db-days-id")

    props = mock_client.pages.update.call_args[1]["properties"]
    assert props["Calories moy/jour"]["number"] == 2200.0
    assert props["Protéines moy/jour"]["number"] == 160.0
    assert props["Glucides moy/jour"]["number"] == 210.0
    assert props["Lipides moy/jour"]["number"] == 70.0
    assert props["Poids moyen"]["number"] == 74.4


def test_update_week_averages_skips_update_when_no_days():
    from notion_service import update_week_averages

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": []}

    update_week_averages(mock_client, "week-id", "db-days-id")

    mock_client.pages.update.assert_not_called()


def test_update_week_averages_filters_by_week_relation():
    from notion_service import update_week_averages

    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = {"results": [
        {"properties": {"Calories": {"number": 2000}, "Proteins": {"number": 150}, "Carbs": {"number": 200}, "Fats": {"number": 60}, "Poids": {"number": 74.0}}},
    ]}

    update_week_averages(mock_client, "week-xyz", "db-days-id")

    call_kwargs = mock_client.data_sources.query.call_args
    assert call_kwargs[0][0] == "db-days-id"
    filter_val = call_kwargs[1]["filter"]
    assert filter_val["property"] == "Week"
    assert filter_val["relation"]["contains"] == "week-xyz"

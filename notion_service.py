import datetime
from typing import Optional

from models import HealthData


def get_monday(date: datetime.date) -> datetime.date:
    return date - datetime.timedelta(days=date.weekday())


def find_week_by_date(client, monday: datetime.date, db_weeks_id: str) -> Optional[str]:
    response = client.data_sources.query(
        db_weeks_id,
        filter={"property": "Date", "date": {"equals": monday.isoformat()}},
    )
    results = response.get("results", [])
    return results[0]["id"] if results else None


def get_next_week_number(client, db_weeks_id: str) -> int:
    response = client.data_sources.query(db_weeks_id)
    weeks = response.get("results", [])
    numbers = []
    for w in weeks:
        parts = w["properties"]["Semaine"]["title"]
        if parts:
            try:
                numbers.append(int(parts[0]["plain_text"].split()[-1]))
            except (ValueError, IndexError):
                pass
    return max(numbers) + 1 if numbers else 1


def create_week_page(client, number: int, monday: datetime.date, db_weeks_id: str) -> str:
    response = client.pages.create(
        parent={"data_source_id": db_weeks_id},
        properties={
            "Semaine": {"title": [{"text": {"content": f"Semaine {number}"}}]},
            "Date": {"date": {"start": monday.isoformat()}},
        },
    )
    return response["id"]


def find_or_create_week(client, date: datetime.date, db_weeks_id: str) -> str:
    monday = get_monday(date)
    page_id = find_week_by_date(client, monday, db_weeks_id)
    if page_id:
        return page_id
    number = get_next_week_number(client, db_weeks_id)
    return create_week_page(client, number, monday, db_weeks_id)


def update_week_averages(client, week_page_id: str, db_days_id: str) -> None:
    response = client.data_sources.query(
        db_days_id,
        filter={"property": "Week", "relation": {"contains": week_page_id}},
    )
    days = response.get("results", [])
    if not days:
        return

    n = len(days)

    def avg(field: str) -> float:
        return round(sum(d["properties"][field]["number"] for d in days) / n, 1)

    client.pages.update(
        page_id=week_page_id,
        properties={
            "Calories moy/jour": {"number": avg("Calories")},
            "Protéines moy/jour": {"number": avg("Proteins")},
            "Glucides moy/jour": {"number": avg("Carbs")},
            "Lipides moy/jour": {"number": avg("Fats")},
        },
    )


def create_day_entry(client, data: HealthData, week_page_id: str, db_days_id: str) -> str:
    response = client.pages.create(
        parent={"data_source_id": db_days_id},
        properties={
            "Name": {
                "title": [{"text": {"content": data.date}}]
            },
            "Date": {
                "date": {"start": data.date}
            },
            "Calories": {"number": data.calories},
            "Proteins": {"number": data.protein_g},
            "Carbs": {"number": data.carbs_g},
            "Fats": {"number": data.fat_g},
            "Week": {
                "relation": [{"id": week_page_id}]
            },
        },
    )
    return response["id"]

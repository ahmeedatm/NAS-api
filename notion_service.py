import datetime
from typing import Optional

import httpx

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


def get_last_weight(client, db_days_id: str) -> Optional[float]:
    response = client.data_sources.query(
        db_days_id,
        filter={"property": "Poids", "number": {"is_not_empty": True}},
        sorts=[{"property": "Date", "direction": "descending"}],
        page_size=1,
    )
    results = response.get("results", [])
    if not results:
        return None
    return results[0]["properties"]["Poids"]["number"]


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

    def avg_nullable(field: str) -> Optional[float]:
        values = [d["properties"][field]["number"] for d in days if d["properties"][field]["number"] is not None]
        return round(sum(values) / len(values), 1) if values else None

    client.pages.update(
        page_id=week_page_id,
        properties={
            "Calories moy/jour": {"number": avg("Calories")},
            "Protéines moy/jour": {"number": avg("Proteins")},
            "Glucides moy/jour": {"number": avg("Carbs")},
            "Lipides moy/jour": {"number": avg("Fats")},
            "Poids moyen": {"number": avg_nullable("Poids")},
        },
    )


_KINE_SPORTS = {"Kiné"}


def get_activity_for_date(client, date: datetime.date, db_workout_id: str) -> str:
    # La base workout est une DB Notion standard (pas un data_source).
    # L'endpoint data_sources/query (API 2025-09-03) ne fonctionne que pour les
    # data sources. On utilise databases/query avec Notion-Version 2022-06-28.
    resp = httpx.post(
        f"https://api.notion.com/v1/databases/{db_workout_id}/query",
        headers={
            "Authorization": f"Bearer {client.options.auth}",
            "Notion-Version": "2022-06-28",
        },
        json={"filter": {"property": "Date", "date": {"equals": date.isoformat()}}},
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return "Repos"
    sport = results[0]["properties"]["Sport"]["select"]["name"]
    if sport in _KINE_SPORTS:
        return "Kiné"
    return "Entrainement"


def create_day_entry(client, data: HealthData, week_page_id: str, db_days_id: str, db_workout_id: str) -> str:
    if data.weight_kg_x10 is not None:
        weight = round(data.weight_kg_x10 / 10, 1)
    else:
        weight = get_last_weight(client, db_days_id)

    activity = get_activity_for_date(client, datetime.date.fromisoformat(data.date), db_workout_id)

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
            "Poids": {"number": weight},
            "Activité": {"status": {"name": activity}},
            "Week": {
                "relation": [{"id": week_page_id}]
            },
        },
    )
    return response["id"]

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A FastAPI gateway that receives daily health metrics from iOS Shortcuts (Apple Health) and writes them to a Notion workspace. The API runs on a NAS and bridges iPhone POST requests to two relational Notion databases.

## Commands

Once implemented, standard commands will be:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

## Environment Variables

Required in `.env`:
- `NOTION_TOKEN` — Notion integration token
- `DB_SEMAINES_ID` — Notion "Weeks" database ID
- `DB_JOURS_ID` — Notion "Days" database ID

## Architecture

**Single endpoint:** `POST /` receives a JSON payload from iOS Shortcuts.

**Payload shape:**
```json
{
  "source": "nutrition",
  "data": {
    "date": "YYYY-MM-DD",
    "calories": 2200,
    "protein_g": 160,
    "carbs_g": 200,
    "fat_g": 70
  }
}
```

**Core logic flow:**
1. Parse and validate the incoming payload
2. Compute the ISO week number from the date
3. If the date is a Monday, create a new "Week XX - YYYY" page in `DB_SEMAINES_ID`; otherwise query for the existing week page
4. Create a new page in `DB_JOURS_ID` with date, calories, macros, and a relation pointing to the week page ID

**Notion database schemas required:**

*Weeks database (`DB_SEMAINES_ID`):*
| Property | Type |
|----------|------|
| Name | title |

*Days database (`DB_JOURS_ID`):*
| Property | Type |
|----------|------|
| Name | title |
| Date | date |
| Calories | number |
| Proteins | number |
| Carbs | number |
| Fats | number |
| Week | relation → Weeks DB |

## Tech Stack

- Python + FastAPI
- `notion-client` (official Notion SDK)
- `python-dotenv` for config
- `pytest` for tests

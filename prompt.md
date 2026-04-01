I want to host a small API on my NAS that will serve as a gateway between iOS Shortcuts (Apple Health) and my Notion workspace.

CONTEXT AND ARCHITECTURE:
1. My iPhone sends every day a JSON payload (POST) containing the day date, my weight, and my macros (protein, carbs, fat).
2. In Notion, I have a database:
The "Weeks" database (each row is a week, e.g. "Week 14 - 2026"). This database has Rollups that compute the average from linked days.
I want to add another relational database associated with Weeks:
The "Days" database (each row is a day). It contains numeric macro/weight properties and a "Relation" property linking to "Weeks".

SCRIPT OBJECTIVE:
I want a script (use Python with FastAPI and the official `notion-client` SDK) that performs the following logic on each POST:

Step 1: Parse the received JSON
Expected format:
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

Step 2: Determine the Week
- From the received date, determine:
    - If Monday: then new week, create a new Week page "Week X" (X is the week number) where macros are stored.
    - Otherwise: use the current week for storing macros.

Step 3: Query the Notion "Weeks" database
- Search the "Weeks" database for a page with the exact title.
- If new week: create the "Week XX" page in "Weeks" and retrieve its `page_id`.
- If current week: simply retrieve the `page_id` for that week.

Step 4: Create the Day entry in Notion
- Create a new item in the "Days" database.
- Set the "Date" property (type: date).
- Set "Calories", "Proteins", "Carbs", "Fats" (type: number).
- Set the relation "Week" to the `page_id` found in Step 3.

CONSTRAINTS AND DELIVERABLES:
- Use environment variables (dotenv) for `NOTION_TOKEN`, `DB_SEMAINES_ID`, and `DB_JOURS_ID`.
- Provide full Python code and a `requirements.txt` file.
- Provide a brief guide on the exact Notion properties to create (exact names and types) so the code works on the first run.
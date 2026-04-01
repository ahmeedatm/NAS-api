import datetime
import os

from dotenv import load_dotenv
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")
from notion_client import Client

from models import HealthPayload
from notion_service import find_or_create_week, create_day_entry, update_week_averages

load_dotenv()

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"422 body received: {body.decode()}")
    logger.error(f"422 detail: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

notion_client = Client(auth=os.environ.get("NOTION_TOKEN", ""))
DB_SEMAINES_ID = os.environ.get("DB_SEMAINES_ID", "")
DB_JOURS_ID = os.environ.get("DB_JOURS_ID", "")


@app.post("/")
async def ingest_health_data(payload: HealthPayload):
    try:
        date = datetime.date.fromisoformat(payload.data.date)
        week_page_id = find_or_create_week(notion_client, date, DB_SEMAINES_ID)
        day_page_id = create_day_entry(notion_client, payload.data, week_page_id, DB_JOURS_ID)
        update_week_averages(notion_client, week_page_id, DB_JOURS_ID)
        return {"status": "ok", "day_page_id": day_page_id}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

from pydantic import BaseModel


class HealthData(BaseModel):
    date: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class HealthPayload(BaseModel):
    source: str
    data: HealthData

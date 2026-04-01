from pydantic import BaseModel


class HealthData(BaseModel):
    date: str
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int


class HealthPayload(BaseModel):
    source: str
    data: HealthData

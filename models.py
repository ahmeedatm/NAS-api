from pydantic import BaseModel


class HealthData(BaseModel):
    date: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    weight_kg_x10: int


class HealthPayload(BaseModel):
    source: str
    data: HealthData

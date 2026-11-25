
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class MedicineCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    brand: Optional[str] = None
    generic_name: str = Field(min_length=2, max_length=150)
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    description: Optional[str] = None


class MedicineResponse(MedicineCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

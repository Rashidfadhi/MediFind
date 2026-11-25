from pydantic import BaseModel, Field, ConfigDict


class InventoryCreate(BaseModel):
    pharmacy_id: int = Field(gt=0)
    medicine_id: int = Field(gt=0)
    quantity: int = Field(ge=0)
    price: float = Field(ge=0)


class InventoryUpdate(BaseModel):
    quantity: int = Field(ge=0)
    price: float = Field(ge=0)


class InventoryResponse(InventoryCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)

# 1. Model vs Schema
#
# SQLAlchemy Model       Pydantic Schema
# Defines DB structure   Defines API data structure
# Creates DB columns     Validates request data
# Communicates with DB   Validates incoming/outgoing data

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


# 2. Pharmacy Create Schema
# Validates incoming pharmacy registration data

class PharmacyCreate(BaseModel):

    name: str = Field(min_length=3, max_length=150)
    address: str = Field(min_length=5, max_length=255)
    landmark: Optional[str] = None

    phone: str = Field(min_length=10, max_length=20)
    email: EmailStr

    latitude: Optional[float] = None
    longitude: Optional[float] = None


# 3. Pharmacy Response Schema
# Defines the pharmacy information returned by the API

class PharmacyResponse(BaseModel):

    id: int
    name: str
    address: str
    landmark: Optional[str] = None

    phone: str
    email: EmailStr

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# 4. Pharmacy Update Schema
# Validates pharmacy update requests

class PharmacyUpdate(BaseModel):

    name: str = Field(min_length=3, max_length=150)
    address: str = Field(min_length=5, max_length=255)
    landmark: Optional[str] = None

    phone: str = Field(min_length=10, max_length=20)
    email: EmailStr

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    is_active: bool = True


from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    brand = Column(String(100), nullable=True)
    generic_name = Column(String(150), nullable=False, index=True)
    strength = Column(String(50), nullable=True)
    dosage_form = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

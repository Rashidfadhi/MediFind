
from sqlalchemy import (
    Column, Integer, ForeignKey, Numeric,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class PharmacyInventory(Base):
    __tablename__ = "pharmacy_inventory"

    id = Column(Integer, primary_key=True, index=True)

    pharmacy_id = Column(
        Integer,
        ForeignKey("pharmacies.id"),
        nullable=False
    )

    medicine_id = Column(
        Integer,
        ForeignKey("medicines.id"),
        nullable=False
    )

    quantity = Column(Integer, default=0, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    pharmacy = relationship("Pharmacy")
    medicine = relationship("Medicine")

    __table_args__ = (
        UniqueConstraint(
            "pharmacy_id",
            "medicine_id",
            name="unique_pharmacy_medicine"
        ),
        CheckConstraint(
            "quantity >= 0",
            name="check_quantity_nonnegative"
        ),
        CheckConstraint(
            "price >= 0",
            name="check_price_nonnegative"
        )
    )

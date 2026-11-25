
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.medicine import MedicineCreate, MedicineResponse
from app.dependencies import require_admin
from app.models.inventory import PharmacyInventory
from app.models.pharmacy import Pharmacy

router = APIRouter(
    prefix="/medicines",
    tags=["Medicines"]
)


# CREATE
@router.post("/", response_model=MedicineResponse, status_code=201)
def create_medicine(
    medicine_data: MedicineCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    new_medicine = Medicine(**medicine_data.model_dump())

    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)

    return new_medicine
@router.get("/search")
def search_medicine(
    medicine: str,
    db: Session = Depends(get_db)
):
    search_term = medicine.strip()

    if len(search_term) < 2:
        raise HTTPException(
            status_code=400,
            detail="Enter at least 2 characters"
        )

    results = (
        db.query(
            Medicine.name.label("medicine"),
            Medicine.generic_name.label("generic_name"),
            Pharmacy.name.label("pharmacy"),
            Pharmacy.address.label("address"),
            Pharmacy.phone.label("phone"),
            Pharmacy.latitude.label("latitude"),
            Pharmacy.longitude.label("longitude"),
            PharmacyInventory.quantity.label("quantity"),
            PharmacyInventory.price.label("price")
        )
        .join(
            PharmacyInventory,
            Medicine.id == PharmacyInventory.medicine_id
        )
        .join(
            Pharmacy,
            Pharmacy.id == PharmacyInventory.pharmacy_id
        )
        .filter(
            (Medicine.name.ilike(f"%{search_term}%") | Medicine.generic_name.ilike(f"%{search_term}%")),
            Pharmacy.is_active == True,
            PharmacyInventory.quantity > 0
        )
        .all()
    )

    return [dict(row._mapping) for row in results]

# READ ALL
@router.get("/", response_model=list[MedicineResponse])
def get_medicines(db: Session = Depends(get_db)):
    return db.query(Medicine).all()



# READ ONE
@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine(
    medicine_id: int,
    db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if medicine is None:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    return medicine



# UPDATE
@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_id: int,
    medicine_data: MedicineCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if medicine is None:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    for field, value in medicine_data.model_dump().items():
        setattr(medicine, field, value)

    db.commit()
    db.refresh(medicine)

    return medicine


# DELETE
@router.delete("/{medicine_id}")
def delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if medicine is None:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    db.delete(medicine)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Remove this medicine from pharmacy inventories before deleting it"
        ) from exc

    return {"message": "Medicine deleted successfully"}


def search_medicine_data(db: Session, medicine: str):

    search_term = medicine.strip()

    if not search_term:
        return []

    results = (
        db.query(
            Medicine.name.label("medicine"),
            Medicine.generic_name.label("generic_name"),
            Pharmacy.name.label("pharmacy"),
            Pharmacy.address.label("address"),
            Pharmacy.landmark.label("landmark"),
            Pharmacy.phone.label("phone"),
            Pharmacy.latitude.label("latitude"),
            Pharmacy.longitude.label("longitude"),
            PharmacyInventory.quantity.label("quantity"),
            PharmacyInventory.price.label("price")
        )
        .join(
            PharmacyInventory,
            Medicine.id == PharmacyInventory.medicine_id
        )
        .join(
            Pharmacy,
            Pharmacy.id == PharmacyInventory.pharmacy_id
        )
        .filter(
            (
                Medicine.name.ilike(f"%{search_term}%")
                |
                Medicine.generic_name.ilike(f"%{search_term}%")
            ),
            Pharmacy.is_active.is_(True),
            PharmacyInventory.quantity > 0
        )
        .all()
    )

    return [dict(row._mapping) for row in results]


import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import PharmacyInventory
from app.models.pharmacy import Pharmacy
from app.models.medicine import Medicine
from app.models.user import User

from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse
)

from app.dependencies import get_current_user


router = APIRouter(
    prefix="/inventory",
    tags=["Pharmacy Inventory"]
)


def validate_inventory_values(quantity: int, price: float):
    if quantity < 0 or not math.isfinite(price) or price < 0 or price > 99999999.99:
        raise HTTPException(status_code=400, detail="Quantity or price is outside the supported range")


# GET THE PHARMACY ASSIGNED TO AN OWNER
def get_owner_pharmacy(current_user: User, db: Session):

    if current_user.role != "pharmacy_owner":
        raise HTTPException(
            status_code=403,
            detail="Pharmacy owner access required"
        )

    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.owner_id == current_user.id,
        Pharmacy.is_active == True
    ).first()

    if not pharmacy:
        raise HTTPException(
            status_code=404,
            detail="No active pharmacy assigned to this owner"
        )

    return pharmacy


# ADD MEDICINE TO INVENTORY
@router.post("/", response_model=InventoryResponse, status_code=201)
def add_inventory(
    data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_inventory_values(data.quantity, data.price)

    # Admin can manage any pharmacy.
    if current_user.role == "admin":
        pharmacy = db.query(Pharmacy).filter(
            Pharmacy.id == data.pharmacy_id,
            Pharmacy.is_active == True
        ).first()

    # Owner can manage only their assigned pharmacy.
    elif current_user.role == "pharmacy_owner":
        pharmacy = get_owner_pharmacy(current_user, db)

        if pharmacy.id != data.pharmacy_id:
            raise HTTPException(
                status_code=403,
                detail="You cannot manage another pharmacy"
            )

    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    if not pharmacy:
        raise HTTPException(
            status_code=404,
            detail="Active pharmacy not found"
        )

    medicine = db.query(Medicine).filter(
        Medicine.id == data.medicine_id
    ).first()

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    existing = db.query(PharmacyInventory).filter(
        PharmacyInventory.pharmacy_id == pharmacy.id,
        PharmacyInventory.medicine_id == data.medicine_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Medicine already exists in this pharmacy inventory"
        )

    new_inventory = PharmacyInventory(
        pharmacy_id=pharmacy.id,
        medicine_id=data.medicine_id,
        quantity=data.quantity,
        price=data.price
    )

    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)

    return new_inventory


# VIEW ALL INVENTORY (PUBLIC)
@router.get("/", response_model=list[InventoryResponse])
def get_inventory(db: Session = Depends(get_db)):

    inventory = (
        db.query(PharmacyInventory)
        .join(Pharmacy)
        .filter(Pharmacy.is_active == True)
        .all()
    )

    return inventory


# VIEW MY PHARMACY INVENTORY (OWNER)
@router.get("/my", response_model=list[InventoryResponse])
def get_my_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    pharmacy = get_owner_pharmacy(current_user, db)

    inventory = db.query(PharmacyInventory).filter(
        PharmacyInventory.pharmacy_id == pharmacy.id
    ).all()

    return inventory


# UPDATE STOCK AND PRICE
@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_inventory_values(data.quantity, data.price)

    inventory = db.query(PharmacyInventory).filter(
        PharmacyInventory.id == inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )

    # Admin can update any inventory.
    if current_user.role == "admin":
        pass

    # Owner can update only their pharmacy inventory.
    elif current_user.role == "pharmacy_owner":

        pharmacy = get_owner_pharmacy(current_user, db)

        if inventory.pharmacy_id != pharmacy.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot update another pharmacy inventory"
            )

    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    inventory.quantity = data.quantity
    inventory.price = data.price

    db.commit()
    db.refresh(inventory)

    return inventory

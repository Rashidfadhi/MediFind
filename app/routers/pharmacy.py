from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


# Import : Purpose
# APIRouter	=Organizes API routes


from app.database import get_db
from app.models.pharmacy import Pharmacy
from app.schemas.pharmacy import PharmacyCreate, PharmacyResponse, PharmacyUpdate
from app.dependencies import require_admin
from app.models.user import User

router = APIRouter(
    prefix="/pharmacies", #all routes start with /pharmacies.
    tags=["Pharmacies"] #grps endpoint in swagger ui
)


@router.post("/", response_model=PharmacyResponse, status_code=201)
def create_pharmacy(
    pharmacy_data: PharmacyCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):

# Important: The admin parameter is intentionally used for authorization. The frontend cannot decide the user's role.
    
    new_pharmacy = Pharmacy(
        name=pharmacy_data.name,
        address=pharmacy_data.address,
        landmark=pharmacy_data.landmark,
        phone=pharmacy_data.phone,
        email=pharmacy_data.email,
        latitude=pharmacy_data.latitude,
        longitude=pharmacy_data.longitude
    )

    db.add(new_pharmacy)
    db.commit()
    db.refresh(new_pharmacy)

    return new_pharmacy
@router.get("/", response_model=list[PharmacyResponse])
def get_pharmacies(db: Session = Depends(get_db)):

    pharmacies = db.query(Pharmacy).filter(
        Pharmacy.is_active == True
    ).all()

    return pharmacies


@router.get("/{pharmacy_id}", response_model=PharmacyResponse)
def get_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db)
):
    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id
    ).first()

    if pharmacy is None:
        raise HTTPException(
            status_code=404,
            detail="Pharmacy not found"
        )

    return pharmacy



@router.put("/{pharmacy_id}", response_model=PharmacyResponse)
def update_pharmacy(
    pharmacy_id: int,
    pharmacy_data: PharmacyUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id
    ).first()

    if pharmacy is None:
        raise HTTPException(
            status_code=404,
            detail="Pharmacy not found"
        )

    pharmacy.name = pharmacy_data.name
    pharmacy.address = pharmacy_data.address
    pharmacy.landmark = pharmacy_data.landmark
    pharmacy.phone = pharmacy_data.phone
    pharmacy.email = pharmacy_data.email
    pharmacy.latitude = pharmacy_data.latitude
    pharmacy.longitude = pharmacy_data.longitude
    pharmacy.is_active = pharmacy_data.is_active

    db.commit()
    db.refresh(pharmacy)

    return pharmacy



@router.delete("/{pharmacy_id}")
def delete_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id
    ).first()

    if pharmacy is None:
        raise HTTPException(
            status_code=404,
            detail="Pharmacy not found"
        )

    pharmacy.is_active = False

    db.commit()
    db.refresh(pharmacy)

    return {
        "message": "Pharmacy deactivated successfully",
        "pharmacy_id": pharmacy.id,
        "is_active": pharmacy.is_active
    }


@router.post("/{pharmacy_id}/assign-owner/{user_id}")
def assign_pharmacy_owner(
    pharmacy_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    # 1. Find pharmacy
    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id
    ).first()

    if not pharmacy:
        raise HTTPException(
            status_code=404,
            detail="Pharmacy not found"
        )

    # 2. Find user
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 3. Prevent assigning admin accounts
    if user.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin cannot become a pharmacy owner"
        )

    # 4. Check whether user owns another pharmacy
    existing_owner = db.query(Pharmacy).filter(
        Pharmacy.owner_id == user.id
    ).first()

    if existing_owner and existing_owner.id != pharmacy.id:
        raise HTTPException(
            status_code=409,
            detail="User already owns another pharmacy"
        )

    # 5. Check whether pharmacy has another owner
    if pharmacy.owner_id and pharmacy.owner_id != user.id:
        raise HTTPException(
            status_code=409,
            detail="Pharmacy already has another owner"
        )

    # 6. Assign owner
    pharmacy.owner_id = user.id
    user.role = "pharmacy_owner"

    db.commit()
    db.refresh(pharmacy)

    return {
        "message": "Pharmacy owner assigned successfully",
        "pharmacy_id": pharmacy.id,
        "owner_id": user.id,
        "owner_name": user.name,
        "owner_role": user.role
    }

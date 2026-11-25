
from fastapi import (
    FastAPI,
    Request,
    Form,
    HTTPException,
    Depends,
    status
)

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from urllib.parse import quote


from sqlalchemy import func
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.security import hash_password, verify_password
from app.database import get_db, Base, engine

from app.models.user import User
from app.models.pharmacy import Pharmacy
from app.models.medicine import Medicine
from app.models.inventory import PharmacyInventory

from app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token
)

from app.dependencies import (
    get_current_user,
    get_current_web_user,
    require_admin,
    require_pharmacy_owner,
    require_web_admin,
    require_web_owner
)

from app.routers.pharmacy import router as pharmacy_routers
from app.routers.medicine import router as medicine_router
from app.routers.inventory import router as inventory_router
from app.routers.medicine import search_medicine_data


# DATABASE INITIALIZATION

Base.metadata.create_all(bind=engine)


# APPLICATION

app = FastAPI(
    title="MediFind API",
    description="Medicine Availability and Pharmacy Finder",
    version="1.0.0"
)


# ROUTERS

app.include_router(pharmacy_routers)
app.include_router(medicine_router)
app.include_router(inventory_router)


# STATIC FILES AND TEMPLATES

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="app/templates"
)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------



@app.get("/")
def home(
    request: Request,
    db: Session = Depends(get_db)
):
    available_medicines = (
        db.query(Medicine)
        .join(
            PharmacyInventory,
            Medicine.id == PharmacyInventory.medicine_id
        )
        .join(
            Pharmacy,
            Pharmacy.id == PharmacyInventory.pharmacy_id
        )
        .filter(
            PharmacyInventory.quantity > 0,
            Pharmacy.is_active == True
        )
        .distinct()
        .order_by(Medicine.name)
        .all()
    )

    print("AVAILABLE MEDICINES:", len(available_medicines))

    for medicine in available_medicines:
        print(
            medicine.id,
            medicine.name,
            medicine.generic_name,
            medicine.strength
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "available_medicines": available_medicines
        }
    )



# --------------------------------------------------
# MEDICINE SEARCH
# --------------------------------------------------

@app.get("/search")
def search_page(
    request: Request,
    medicine: str = "",
    db: Session = Depends(get_db)
):

    results = []
    error = None

    medicine = medicine.strip()

    if medicine:

        if len(medicine) < 3:
            error = "Medicine name must contain at least 3 characters."

        else:
            results = search_medicine_data(db, medicine)

    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={
            "medicine": medicine,
            "results": results,
            "error": error
        }
    )




@app.get("/medicine/search")
def medicine_search(
    request: Request,
    medicine: str = "",
    db: Session = Depends(get_db)
):

    medicine = medicine.strip()

    if not medicine:
        return templates.TemplateResponse(
            request=request,
            name="search_results.html",
            context={
                "medicine": "",
                "results": [],
                "error": "Please enter a medicine name."
            }
        )

    if len(medicine) < 3:
        return templates.TemplateResponse(
            request=request,
            name="search_results.html",
            context={
                "medicine": medicine,
                "results": [],
                "error": "Medicine name must contain at least 3 characters."
            }
        )

    results = search_medicine_data(db, medicine)

    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={
            "medicine": medicine,
            "results": results,
            "error": None
        }
    )


# --------------------------------------------------
# CUSTOMER REGISTRATION PAGE
# --------------------------------------------------

@app.get("/registration")
def registration_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": None}
    )


# --------------------------------------------------
# CUSTOMER REGISTRATION API
# --------------------------------------------------

@app.post("/register")
def register_customer(
    name: str = Form(),
    email: str = Form(),
    password: str = Form(),
    age: int = Form(),
    db: Session = Depends(get_db)
):

    name = name.strip()
    email = email.strip().lower()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty"
        )

    if age < 18:
        raise HTTPException(
            status_code=400,
            detail="You must be at least 18"
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        age=age,
        role="customer"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )

    return {
        "message": "Customer registration successful",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role
    }


# --------------------------------------------------
# API LOGIN - BEARER TOKEN
# --------------------------------------------------

@app.post("/login")
def api_login(
    email: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if not user or not verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# --------------------------------------------------
# USER PROFILE
# --------------------------------------------------

@app.get("/profile")
def profile(
    current_user: User = Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


# --------------------------------------------------
# ADMIN API DASHBOARD
# --------------------------------------------------

@app.get("/admin/dashboard")
def admin_api_dashboard(
    admin: User = Depends(require_admin)
):

    return {
        "message": "Welcome Admin!",
        "name": admin.name,
        "role": admin.role
    }


# --------------------------------------------------
# OWNER API DASHBOARD
# --------------------------------------------------

@app.get("/api/owner/dashboard")
def owner_api_dashboard(
    owner: User = Depends(require_pharmacy_owner)
):

    return {
        "message": "Welcome Pharmacy Owner!",
        "owner_id": owner.id,
        "name": owner.name,
        "role": owner.role
    }


# --------------------------------------------------
# HELPER: GET OWNER PHARMACY
# --------------------------------------------------

def get_owner_pharmacy(
    owner: User,
    db: Session
):

    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.owner_id == owner.id,
        Pharmacy.is_active == True
    ).first()

    if not pharmacy:
        raise HTTPException(
            status_code=404,
            detail="No active pharmacy assigned to this owner"
        )

    return pharmacy


# --------------------------------------------------
# ADMIN WEB DASHBOARD
# --------------------------------------------------

@app.get("/web/admin/dashboard")
def admin_dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):

    total_users = db.query(User).count()

    total_pharmacies = db.query(Pharmacy).count()

    total_medicines = db.query(Medicine).count()

    total_inventory = db.query(
        PharmacyInventory
    ).count()

    pharmacy_data = (
        db.query(Pharmacy, User.name)
        .outerjoin(
            User,
            Pharmacy.owner_id == User.id
        )
        .order_by(Pharmacy.id.desc())
        .all()
    )

    pharmacy_rows = [
        {
            "pharmacy": pharmacy,
            "owner_name": owner_name or "Not assigned"
        }
        for pharmacy, owner_name in pharmacy_data
    ]

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "admin": admin,
            "total_users": total_users,
            "total_pharmacies": total_pharmacies,
            "total_medicines": total_medicines,
            "total_inventory": total_inventory,
            "pharmacy_rows": pharmacy_rows
        }
    )


# ==========================================
# ADMIN MANAGE OWNERS PAGE
# ==========================================

@app.get("/web/admin/owners")
def admin_owners_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    # Get all pharmacy owners
    owners = db.query(User).filter(
        User.role == "pharmacy_owner"
    ).order_by(User.id.desc()).all()

    # Attach each owner's assigned pharmacy
    for owner in owners:
        owner.pharmacy = db.query(Pharmacy).filter(
            Pharmacy.owner_id == owner.id
        ).first()

    return templates.TemplateResponse(
        request=request,
        name="admin_owners.html",
        context={
            "admin": admin,
            "owners": owners
        }
    )

# --------------------------------------------------
# OWNER WEB DASHBOARD
# --------------------------------------------------

@app.get("/owner/dashboard")
def owner_dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    owner: User = Depends(require_web_owner)
):

    pharmacy = get_owner_pharmacy(owner, db)

    total_medicines = db.query(
        func.count(PharmacyInventory.id)
    ).filter(
        PharmacyInventory.pharmacy_id == pharmacy.id
    ).scalar() or 0

    total_quantity = db.query(
        func.sum(PharmacyInventory.quantity)
    ).filter(
        PharmacyInventory.pharmacy_id == pharmacy.id
    ).scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="owner_dashboard.html",
        context={
            "owner": owner,
            "pharmacy": pharmacy,
            "total_medicines": total_medicines,
            "total_quantity": total_quantity
        }
    )


# --------------------------------------------------
# OWNER INVENTORY PAGE
# --------------------------------------------------

@app.get("/owner/inventory")
def owner_inventory_page(
    request: Request,
    db: Session = Depends(get_db),
    owner: User = Depends(require_web_owner)
):

    pharmacy = get_owner_pharmacy(owner, db)

    inventory = db.query(
        PharmacyInventory
    ).filter(
        PharmacyInventory.pharmacy_id == pharmacy.id
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="owner_inventory.html",
        context={
            "owner": owner,
            "pharmacy": pharmacy,
            "inventory": inventory
        }
    )


# --------------------------------------------------
# OWNER ADD INVENTORY
# --------------------------------------------------

@app.post("/owner/inventory/add")
def owner_add_inventory(
    medicine_id: int = Form(),
    quantity: int = Form(),
    price: float = Form(),
    db: Session = Depends(get_db),
    owner: User = Depends(require_web_owner)
):

    pharmacy = get_owner_pharmacy(owner, db)

    if quantity < 0 or price < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity and price cannot be negative"
        )

    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    existing = db.query(PharmacyInventory).filter(
        PharmacyInventory.pharmacy_id == pharmacy.id,
        PharmacyInventory.medicine_id == medicine_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Medicine already exists. Update its stock instead."
        )

    new_item = PharmacyInventory(
        pharmacy_id=pharmacy.id,
        medicine_id=medicine_id,
        quantity=quantity,
        price=price
    )

    try:
        db.add(new_item)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not add inventory"
        )

    return RedirectResponse(
        url="/owner/inventory?success=Inventory+added+successfully",
        status_code=303
    )


# --------------------------------------------------
# OWNER UPDATE INVENTORY
# --------------------------------------------------

@app.post("/owner/inventory/update/{inventory_id}")
def owner_update_inventory(
    inventory_id: int,
    quantity: int = Form(),
    price: float = Form(),
    db: Session = Depends(get_db),
    owner: User = Depends(require_web_owner)
):

    pharmacy = get_owner_pharmacy(owner, db)

    if quantity < 0 or price < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity and price cannot be negative"
        )

    inventory = db.query(
        PharmacyInventory
    ).filter(
        PharmacyInventory.id == inventory_id,
        PharmacyInventory.pharmacy_id == pharmacy.id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )

    inventory.quantity = quantity
    inventory.price = price

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Inventory update failed"
        )

    return RedirectResponse(
        url="/owner/inventory?success=Stock+updated+successfully",
        status_code=303
    )


# --------------------------------------------------
# WEB LOGIN PAGE
# --------------------------------------------------

@app.get("/web/login")
def web_login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None}
    )


# --------------------------------------------------
# WEB LOGIN
# --------------------------------------------------

@app.post("/web/login")
def web_login(
    request: Request,
    email: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if not user or not verify_password(
        password,
        user.hashed_password
    ):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Invalid email or password"
            },
            status_code=401
        )

    token = create_access_token(
        data={"sub": str(user.id)}
    )

    if user.role == "admin":
        destination = "/web/admin/dashboard"

    elif user.role == "pharmacy_owner":
        destination = "/owner/dashboard"

    else:
        destination = "/"

    response = RedirectResponse(
        url=destination,
        status_code=status.HTTP_303_SEE_OTHER
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return response


# ==========================================
# WEB CUSTOMER REGISTRATION
# ==========================================

@app.post("/web/register")
def web_register_customer(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    age: int = Form(...),
    db: Session = Depends(get_db)
):
    name = name.strip()
    email = email.strip().lower()

    if not name:
        return RedirectResponse(
            "/registration?error=invalid",
            status_code=303
        )

    if age < 18:
        return RedirectResponse(
            "/registration?error=age",
            status_code=303
        )

    if age > 120:
        return RedirectResponse(
            "/registration?error=invalid",
            status_code=303
        )

    if len(password) < 8:
        return RedirectResponse(
            "/registration?error=password",
            status_code=303
        )

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        return RedirectResponse(
            "/registration?error=email",
            status_code=303
        )

    new_user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        age=age,
        role="customer"
    )

    try:
        db.add(new_user)
        db.commit()

    except Exception:
        db.rollback()
        return RedirectResponse(
            "/registration?error=invalid",
            status_code=303
        )

    return RedirectResponse(
        "/web/login?registered=success",
        status_code=303
    )

# --------------------------------------------------
# WEB LOGOUT
# --------------------------------------------------

@app.get("/web/logout")
def web_logout():

    response = RedirectResponse(
        url="/web/login",
        status_code=303
    )

    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return response



# ==========================================
# ADMIN PHARMACY MANAGEMENT
# ==========================================

@app.get("/web/admin/pharmacies")
def admin_pharmacies_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    pharmacies = db.query(Pharmacy).order_by(
        Pharmacy.id.desc()
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_pharmacies.html",
        context={
            "admin": admin,
            "pharmacies": pharmacies
        }
    )


@app.post("/web/admin/pharmacies/add")
def admin_add_pharmacy(
    name: str = Form(),
    address: str = Form(),
    landmark: str = Form(""),
    phone: str = Form(),
    email: str = Form(),
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    email = email.strip().lower()

    if not name.strip() or not address.strip() or not phone.strip():
        raise HTTPException(400, "Required fields cannot be empty")

    if db.query(Pharmacy).filter(
        Pharmacy.email == email
    ).first():
        raise HTTPException(409, "Pharmacy email already exists")

    pharmacy = Pharmacy(
        name=name.strip(),
        address=address.strip(),
        landmark=landmark.strip() or None,
        phone=phone.strip(),
        email=email,
        is_active=True
    )

    db.add(pharmacy)
    db.commit()

    return RedirectResponse(
        "/web/admin/pharmacies?success=Pharmacy+added",
        status_code=303
    )


@app.post("/web/admin/pharmacies/update/{pharmacy_id}")
def admin_update_pharmacy(
    pharmacy_id: int,
    name: str = Form(),
    address: str = Form(),
    landmark: str = Form(""),
    phone: str = Form(),
    email: str = Form(),
    is_active: bool = Form(False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id
    ).first()

    if not pharmacy:
        raise HTTPException(404, "Pharmacy not found")

    email = email.strip().lower()

    duplicate = db.query(Pharmacy).filter(
        Pharmacy.email == email,
        Pharmacy.id != pharmacy_id
    ).first()

    if duplicate:
        raise HTTPException(409, "Email already used by another pharmacy")

    pharmacy.name = name.strip()
    pharmacy.address = address.strip()
    pharmacy.landmark = landmark.strip() or None
    pharmacy.phone = phone.strip()
    pharmacy.email = email
    pharmacy.is_active = is_active

    db.commit()

    return RedirectResponse(
        "/web/admin/pharmacies?success=Pharmacy+updated",
        status_code=303
    )


@app.post("/web/admin/pharmacies/delete/{pharmacy_id}")
def admin_delete_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    pharmacy = db.query(Pharmacy).filter(
        Pharmacy.id == pharmacy_id
    ).first()

    if not pharmacy:
        raise HTTPException(404, "Pharmacy not found")

    # Soft delete: preserve historical records
    pharmacy.is_active = False
    db.commit()

    return RedirectResponse(
        "/web/admin/pharmacies?success=Pharmacy+deactivated",
        status_code=303
    )



# ==========================================
# ADMIN MEDICINE MANAGEMENT
# ==========================================

@app.get("/web/admin/medicines")
def admin_medicines_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    medicines = db.query(Medicine).order_by(
        Medicine.id.desc()
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_medicines.html",
        context={
            "admin": admin,
            "medicines": medicines
        }
    )


# ADD MEDICINE
@app.post("/web/admin/medicines/add")
def admin_add_medicine(
    name: str = Form(),
    brand: str = Form(""),
    generic_name: str = Form(),
    strength: str = Form(""),
    dosage_form: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    if not name.strip() or not generic_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Medicine name and generic name are required"
        )

    medicine = Medicine(
        name=name.strip(),
        brand=brand.strip() or None,
        generic_name=generic_name.strip(),
        strength=strength.strip() or None,
        dosage_form=dosage_form.strip() or None,
        description=description.strip() or None
    )

    try:
        db.add(medicine)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not add medicine"
        )

    return RedirectResponse(
        url="/web/admin/medicines?success=Medicine+added",
        status_code=303
    )


# UPDATE MEDICINE
@app.post("/web/admin/medicines/update/{medicine_id}")
def admin_update_medicine(
    medicine_id: int,
    name: str = Form(),
    brand: str = Form(""),
    generic_name: str = Form(),
    strength: str = Form(""),
    dosage_form: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    if not name.strip() or not generic_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Medicine name and generic name are required"
        )

    medicine.name = name.strip()
    medicine.brand = brand.strip() or None
    medicine.generic_name = generic_name.strip()
    medicine.strength = strength.strip() or None
    medicine.dosage_form = dosage_form.strip() or None
    medicine.description = description.strip() or None

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update medicine"
        )

    return RedirectResponse(
        url="/web/admin/medicines?success=Medicine+updated",
        status_code=303
    )


# DELETE MEDICINE
@app.post("/web/admin/medicines/delete/{medicine_id}")
def admin_delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_web_admin)
):
    medicine = db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    # Prevent deletion if inventory records reference it
    inventory_record = db.query(PharmacyInventory).filter(
        PharmacyInventory.medicine_id == medicine_id
    ).first()

    if inventory_record:
        raise HTTPException(
            status_code=409,
            detail="This medicine is linked to pharmacy inventory. "
                   "Remove its inventory records before deleting it."
        )

    try:
        db.delete(medicine)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Medicine could not be deleted"
        )

    return RedirectResponse(
        url="/web/admin/medicines?success=Medicine+deleted",
        status_code=303
    )


from fastapi import Depends, HTTPException, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.config import SECRET_KEY, ALGORITHM
from app.database import get_db
from app.models.user import User


bearer_scheme = HTTPBearer()


def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not isinstance(user_id, str) or not user_id.isdigit():
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# API authentication: Bearer token
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    return get_user_from_token(credentials.credentials, db)


# Website authentication: HTTP-only cookie
def get_current_web_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )

    return get_user_from_token(access_token, db)


def require_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


def require_pharmacy_owner(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "pharmacy_owner":
        raise HTTPException(
            status_code=403,
            detail="Pharmacy owner access required"
        )

    return current_user


def require_web_admin(
    current_user: User = Depends(get_current_web_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


def require_web_owner(
    current_user: User = Depends(get_current_web_user)
):
    if current_user.role != "pharmacy_owner":
        raise HTTPException(
            status_code=403,
            detail="Pharmacy owner access required"
        )

    return current_user

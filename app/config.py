
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import HTTPException
from jose import jwt

# Load environment variables from .env
load_dotenv()

SECRET_KEY = os.getenv("MEDIFIND_SECRET_KEY", "")
ALGORITHM = "HS256"

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("MEDIFIND_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
except ValueError as exc:
    raise RuntimeError(
        "MEDIFIND_ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer"
    ) from exc

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "MEDIFIND_ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer"
    )


def create_access_token(data: dict):
    if len(SECRET_KEY) < 32:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured. "
                   "Set MEDIFIND_SECRET_KEY to a random value "
                   "of at least 32 characters."
        )

    payload = data.copy()

    payload["exp"] = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

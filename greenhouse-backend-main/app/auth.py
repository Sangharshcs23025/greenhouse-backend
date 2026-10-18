from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Query
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_current_user_email(authorization: str = Header(...)) -> str:
    """Dependency: extracts and validates the JWT from the Authorization header
    (used by every Flutter-app-facing endpoint)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return email


async def get_optional_user_email(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> Optional[str]:
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ", 1)[1]
    elif token:
        raw_token = token
    if not raw_token:
        return None
    try:
        payload = decode_access_token(raw_token)
        return payload.get("sub")
    except Exception:
        return None


async def verify_device_key(x_device_key: str = Header(...)) -> None:
    """Dependency: the ESP32 sends this header instead of a JWT."""
    if x_device_key != settings.device_api_key:
        raise HTTPException(status_code=401, detail="Invalid device key")
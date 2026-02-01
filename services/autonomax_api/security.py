from __future__ import annotations

from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from .settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 24  # 24h

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.effective_secret(), algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.effective_secret(), algorithms=[ALGORITHM])

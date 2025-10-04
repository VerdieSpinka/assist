# server/services/auth_service.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# --- PERUBAHAN DI SINI: Konfigurasi JWT yang Lebih Aman ---
# Gunakan variabel lingkungan untuk SECRET_KEY. Jika tidak ada, gunakan default yang tetap (bukan acak).
# PENTING: Untuk produksi, SELALU atur SECRET_KEY di lingkungan Anda.
SECRET_KEY = os.getenv("SECRET_KEY", "your-default-super-secret-key-for-development")
ALGORITHM = "HS256"
# Buat masa berlaku token dapat dikonfigurasi melalui variabel lingkungan
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)) # Default 7 hari

pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")
# --- AKHIR PERUBAHAN ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
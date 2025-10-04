# server/routers/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any

from services.db_service import db_service
from services.auth_service import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # Bcrypt memiliki batasan 72 byte. Kita batasi di 70 karakter untuk keamanan.
        # Karakter non-ASCII bisa memakan lebih dari 1 byte.
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must not exceed 72 bytes.')
        return v

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: User

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = await db_service.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    db_user_by_username = await db_service.get_user_by_username(user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Kita perlu menambahkan fungsi get_user_by_email di db_service.py
    # db_user_by_email = await db_service.get_user_by_email(user.email)
    # if db_user_by_email:
    #     raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    
    user_id = await db_service.create_user(user.username, user.email, hashed_password, role='user')
    
    return {"id": user_id, "username": user.username, "email": user.email, "role": "user"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db_service.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user['id'])})
    user_model = User(id=user['id'], username=user['username'], email=user['email'], role=user['role'])
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_model}

@router.get("/me", response_model=User)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user
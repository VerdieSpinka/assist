# server/routers/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Dict, Any, Optional

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
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must not exceed 72 bytes.')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    image_url: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must not exceed 72 bytes.')
        return v
        
class ProfilePictureUpdate(BaseModel):
    file_id: str

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    image_url: Optional[str] = None
    credits: int

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
    
    db_user_by_email = await db_service.get_user_by_email(user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    
    user_id = await db_service.create_user(user.username, user.email, hashed_password, role='user')
    
    # Pengguna baru akan mendapatkan 10 kredit dari default database
    return User(id=user_id, username=user.username, email=user.email, role="user", image_url=None, credits=10)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # ... (logika login)
    user = await db_service.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user['id'])})
    user_model = User(id=user['id'], username=user['username'], email=user['email'], role=user['role'], image_url=user.get('image_url'), credits=user.get('credits', 0))
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_model}

@router.get("/me", response_model=User)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=User)
async def update_user_me(user_update: UserUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    update_data = user_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    # Check for uniqueness if username/email are being changed
    if "username" in update_data and update_data["username"] != current_user["username"]:
        if await db_service.get_user_by_username(update_data["username"]):
            raise HTTPException(status_code=400, detail="Username already taken")
    if "email" in update_data and update_data["email"] != current_user["email"]:
        if await db_service.get_user_by_email(update_data["email"]):
            raise HTTPException(status_code=400, detail="Email already registered")

    updated_user = await db_service.update_user_profile(current_user['id'], update_data)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Could not update user profile")
        
    return updated_user

@router.post("/me/change-password")
async def change_password(password_data: PasswordChange, current_user: Dict[str, Any] = Depends(get_current_user)):
    if not verify_password(password_data.current_password, current_user['hashed_password']):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    new_hashed_password = get_password_hash(password_data.new_password)
    await db_service.update_user_password(current_user['id'], new_hashed_password)
    
    return {"message": "Password updated successfully"}

@router.post("/me/profile-picture", response_model=User)
async def update_profile_picture(data: ProfilePictureUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
    from common import DEFAULT_PORT
    image_url = f"http://localhost:{DEFAULT_PORT}/api/file/{data.file_id}"
    update_data = {"image_url": image_url}
    
    updated_user = await db_service.update_user_profile(current_user['id'], update_data)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Could not update profile picture")
        
    return updated_user
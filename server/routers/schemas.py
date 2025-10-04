from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        # Sebelumnya orm_mode = True, sekarang from_attributes = True di Pydantic v2
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: User

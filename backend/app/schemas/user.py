from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.models.user import RoleEnum


# -------------------------
# Request Schemas
# -------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role: RoleEnum = RoleEnum.Driver


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    full_name: str
    phone: str | None = None


class EmailUpdate(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# -------------------------
# Response Schemas
# -------------------------

class UserResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    role: RoleEnum = RoleEnum.Driver
    email_verified: bool

    class Config:
        from_attributes = True


class UserManagementCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=15)
    address: str | None = Field(default=None, max_length=255)
    role: RoleEnum


class UserManagementUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=15)
    address: str | None = Field(default=None, max_length=255)
    role: RoleEnum | None = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserManagementResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    role: RoleEnum
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserManagementResponse]
    total: int
    skip: int
    limit: int


# -------------------------
# JWT Schemas
# -------------------------

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None

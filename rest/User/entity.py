from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from app.db.schema.Base import LanguageCode, LanguageLevel, Role


class UserCreateRequest(BaseModel):
    token: bytes
    id: int


class User(BaseModel):
    id: str
    telegram_id: Optional[int]
    email: str
    email_verified: bool
    password: str
    created_at: datetime
    disabled: bool
    role: Role

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    name: str
    balance: int
    role: Role


class APIUserResponse(BaseModel):
    status: Literal['ok'] = 'ok'
    data: UserResponse


class APIUserListResponse(BaseModel):
    status: Literal['ok'] = 'ok'
    data: list[UserResponse]


class UserProfileResponse(BaseModel):
    name: Optional[str] = None
    target: Optional[str] = None
    interests: Optional[list[str]] = None
    language_level: LanguageLevel
    next_language_level: Optional[LanguageLevel] = None
    subscription_until: Optional[datetime] = None
    progress: float = 0
    days_in_row: Optional[int] = 0
    referral_code: Optional[str] = None
    is_onboarded: bool = False

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    target: Optional[str] = None
    interests: Optional[list[str]] = None
    language_level: Optional[LanguageLevel] = None
    progress: Optional[float] = None


class UserProfileRegistrationRequest(BaseModel):
    name: str


class UserProfileRegistrationResponse(BaseModel):
    detail: str


class UserProfileUpdateResponse(BaseModel):
    detail: str


class UserProfileLanguageLevelNone(BaseModel):
    detail: str = "Language level none"

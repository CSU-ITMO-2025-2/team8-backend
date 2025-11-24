from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, constr, model_validator

from jwt_auth.auth_jwt import TokenType


class TelegramLinkForm(BaseModel):
    email: EmailStr
    code: int


class UserAuthenticationForm(BaseModel):
    email: str
    password: str


class UserRegistrationForm(BaseModel):
    login: Optional[constr(
        min_length=4,
        max_length=20
    )]
    password: Optional[constr(
        min_length=4,
        max_length=20
    )]

class TokenResponse(BaseModel):
    token: str
    type: TokenType


class WebTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    email_verified: Optional[bool] = None
    token_type: str = "bearer"


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    email_verified: Optional[bool] = None


class TokenData(BaseModel):
    user_id: str
    token_type: TokenType


class TokenInDB(BaseModel):
    id: int
    user_id: str
    token: str
    device: str
    last_action: datetime


class ConfirmCodeRequest(BaseModel):
    code: int


class EmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    password: constr(
        min_length=6,
        max_length=20
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str

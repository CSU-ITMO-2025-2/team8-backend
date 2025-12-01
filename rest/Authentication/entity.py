from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, constr, model_validator, Field


class UserRegistrationForm(BaseModel):
    login: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=4, max_length=20)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
from pydantic import BaseModel, Field


class UserRegistrationForm(BaseModel):
    login: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=4, max_length=20)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
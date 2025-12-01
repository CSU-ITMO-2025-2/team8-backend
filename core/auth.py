import inspect
from base64 import b64encode
from functools import lru_cache

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, HTTPBasicCredentials, HTTPBasic

from dal import Database
from dal.schema.Entity.BackendSchema import User

from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

security = HTTPBasic()


class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Basic"},
        )


class BasicAuth:

    @staticmethod
    def create_token(login, password):
        return f"Basic {b64encode(f'{login}:{password}'.encode()).decode()}"

    @staticmethod
    async def token_auth(credentials: HTTPBasicCredentials = Depends(security)):
        return await BasicAuth.auth(credentials.username, credentials.password)

    @staticmethod
    async def auth(login, password) -> User:
        user = await Database.AuthService.get_user(login=login)

        try:
            if pwd_context.verify(password, user.hashed_password):
                return user
            raise
        except:
            raise AuthenticationError("Invalid login or password")






if __name__ == '__main__':
    test_token = BasicAuth.create_token("username", "password")
    pass
import uuid
from calendar import timegm
from datetime import datetime, timezone
from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status

from .auth_config import AuthConfig
from .exceptions import AuthenticateUserError, ValidateCredentialsError, UserNotFound
from ..db.DAO import DAO
from ..db.schema.Base import TokenType, Role
from ..rest.Authentication.entity import TokensResponse, TokenData, RefreshTokenRequest
from ..rest.User.entity import User


class AuthJWT(AuthConfig):
    blacklist = set()
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

    @classmethod
    async def authenticate_user(cls, email: str, password: str):
        user = await DAO().User.get(email)
        if user:
            if user.password != "":
                if cls.verify_value(password, user.password):
                    return user
        raise AuthenticateUserError(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Incorrect username or password", )

    @classmethod
    def hash_value(cls, password):
        return cls._pwd_context.hash(password)

    @classmethod
    def verify_value(cls, plain_password, hashed_password):
        return cls._pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def create_token(cls, data: dict, token_type: TokenType):
        to_encode = data.copy()
        to_encode["type"] = token_type.value
        if token_type == TokenType.ACCESS_TOKEN:
            to_encode["exp"] = datetime.now(timezone.utc) + cls._access_token_expires
        elif token_type in (TokenType.CODE_CONFIRMATION, TokenType.PASSWORD_RESET):
            to_encode["exp"] = datetime.now(timezone.utc) + cls._reset_token_expires
        encoded_jwt = jwt.encode(to_encode, cls._secret_key, algorithm=cls._algorithm)
        return encoded_jwt

    @classmethod
    def create_tokens(cls, data: dict):
        access_token = cls.create_token(data, TokenType.ACCESS_TOKEN)
        refresh_token = cls.create_token(data, TokenType.REFRESH_TOKEN)
        return TokensResponse(access_token=access_token, refresh_token=refresh_token, email_verified=False)

    @staticmethod
    def generate_session_key() -> str:
        return uuid.uuid4().hex

    @classmethod
    async def set_session_key(cls, user_id: str, session_key: str = generate_session_key()):
        result = await DAO().User.set_session_key(user_id, session_key)
        if result.rowcount == 0:
            return False
        return session_key


async def validate_token(token: Annotated[str, Depends(AuthJWT.oauth2_scheme)]):
    try:
        payload = jwt.decode(token, AuthJWT._secret_key, algorithms=AuthJWT._algorithm, options={"verify_exp": False})
        user_id = payload.get("sub")
        session_key = payload.get("sid")
        token_type = TokenType(payload.get("type"))

        if token_type != TokenType.REFRESH_TOKEN:
            exp = int(payload.get("exp"))
            if exp < timegm(datetime.now(timezone.utc).utctimetuple()):
                raise ValidateCredentialsError()

        if token_type == TokenType.CODE_CONFIRMATION:
            return TokenData(user_id=user_id, session_key=session_key, token_type=token_type)

        if token_type == TokenType.PASSWORD_RESET:
            jti = payload.get("jti")
            if jti in AuthJWT.blacklist:
                raise ValidateCredentialsError()
            AuthJWT.blacklist.add(jti)
            return TokenData(user_id=user_id, session_key=session_key, token_type=token_type)

        if None in (user_id, session_key, token_type):
            raise ValidateCredentialsError()

        return TokenData(user_id=user_id, session_key=session_key, token_type=token_type)

    except JWTError:
        raise ValidateCredentialsError()


async def tg_validate_token(token: Annotated[str, Depends(AuthJWT.oauth2_scheme)]) -> int:
    try:
        payload = jwt.decode(token, AuthJWT._tg_secret_key, algorithms=AuthJWT._algorithm, options={"verify_exp": False})
        tg_id = payload.get("tg_id")

        try:
            tg_id: int = int(tg_id)
        except ValueError:
            raise ValidateCredentialsError()

        exp = int(payload.get("exp"))
        if exp < timegm(datetime.now(timezone.utc).utctimetuple()):
            raise ValidateCredentialsError()
        if tg_id is None:
            raise ValidateCredentialsError()
        return tg_id
    except JWTError as e:
        raise ValidateCredentialsError()


async def get_token(token: Annotated[str, Depends(AuthJWT.oauth2_scheme)]):
    return token


async def get_user(user_id: str, session_key: str) -> User:
    user = await DAO().User.get(user_id=user_id)
    if user is None:
        raise UserNotFound()
    if user.session_key != session_key:
        raise ValidateCredentialsError()
    return user


async def get_refresh_token(token: RefreshTokenRequest):
    token_data = await validate_token(token.refresh_token)
    if token_data.token_type != TokenType.REFRESH_TOKEN:
        raise ValidateCredentialsError(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong token type")
    await get_current_active_user(await get_user(token_data.user_id, token_data.session_key))
    return token_data


async def get_current_user(token_data: Annotated[TokenData, Depends(validate_token)]):
    if token_data.token_type != TokenType.ACCESS_TOKEN:
        raise ValidateCredentialsError(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong token type")
    return await get_user(token_data.user_id, token_data.session_key)


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    # if not current_user.email_verified:
    #     raise HTTPException(status_code=400, detail="Email not verified")
    return current_user


async def get_admin_user(current_user: Annotated[User, Depends(get_current_active_user)]):
    if not current_user.role == Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# async def get_current_active_user_not_email(current_user: Annotated[User, Depends(get_current_user)]):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user

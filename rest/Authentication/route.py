import random
from typing import Annotated

from fastapi import HTTPException, Request, APIRouter
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from user_agents import parse

from dal import Database
from dal.database.DatabaseAuthService import UserAlreadyExistsError
from dal.schema.Entity.BackendSchema import User as UserBase
from entity import TokensResponse, RefreshTokenRequest, UserAuthenticationForm, WebTokenResponse, UserRegistrationForm, \
    TelegramLinkForm
from jwt_auth import AuthJWT


class Authentication:

    def __init__(self):
        self.route = APIRouter(prefix="/user", tags=["Authentication"])
        self.route.add_api_route("/login", self.web_auth, methods=["POST"], response_model=WebTokenResponse,
                                 responses={
                                     401: {
                                         "description": "ErrorAuthentication",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Incorrect username or password"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/token", self.rest_auth, methods=["POST"], response_model=TokensResponse,
                                 responses={
                                     401: {
                                         "description": "ErrorAuthentication",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Incorrect username or password"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/registration", self.registration, methods=["POST"], response_model=int,
                                 responses={
                                     409: {
                                         "description": "ErrorCreateUser",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Already registered"
                                                     }
                                                 }
                                             }
                                     },
                                     500: {
                                         "description": "ErrorCreateUser",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Error register User."
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/refresh", self.refresh_access_token, methods=["POST"], response_model=TokensResponse)

    @staticmethod
    async def refresh_access_token(refresh_token_request: RefreshTokenRequest,
                                   authorize: AuthJWT = Depends()):
        refresh_token_data = await get_refresh_token(refresh_token_request)
        user = await get_user(user_id=refresh_token_data.user_id)
        access_token = authorize.create_token(data={"sub": refresh_token_data.user_id,
                                                    "sid": refresh_token_data.session_key},
                                              token_type=TokenType.ACCESS_TOKEN)
        return TokensResponse(access_token=access_token, refresh_token=refresh_token_request.refresh_token,
                              email_verified=user.email_verified)

    @staticmethod
    async def authenticate(form_data: OAuth2PasswordRequestForm | UserAuthenticationForm | int,
                           request: Request,
                           authorize: AuthJWT = Depends()) -> TokensResponse:
        if isinstance(form_data, OAuth2PasswordRequestForm):
            user: UserBase = await authorize.authenticate_user(form_data.username, form_data.password)
        else:
            user: UserBase = await authorize.authenticate_user(form_data.email, form_data.password)
        response = authorize.create_tokens(data={"sub": user.id
                                                 })
        return response

    async def web_auth(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                       request: Request,
                       authorize: AuthJWT = Depends()) -> WebTokenResponse:
        tokens_response = await self.authenticate(form_data, request, authorize)
        return WebTokenResponse(access_token=tokens_response.access_token, refresh_token=tokens_response.refresh_token, email_verified=tokens_response.email_verified, token_type="bearer")

    async def rest_auth(self, form_data: UserAuthenticationForm, request: Request,
                        authorize: AuthJWT = Depends()
                        ) -> TokensResponse:
        return await self.authenticate(form_data, request, authorize)


    @staticmethod
    async def registration(form_data: UserRegistrationForm, request: Request,
                           authorize: AuthJWT = Depends()) -> WebTokenResponse:
        try:
            user = await Database.AuthService.register_user(
                login=form_data.login,
                password=form_data.password,
            )
        except UserAlreadyExistsError:
            # 409 уже описан в responses
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already registered",
            )
        except Exception:
            # можно залогировать и отдать 500
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error register User.",
            )

        tokens = authorize.create_tokens(data={"sub": str(user.id)})

        return WebTokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
        )


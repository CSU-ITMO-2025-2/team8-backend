
from fastapi import HTTPException, Request, APIRouter
from fastapi.security import HTTPBasic
from starlette import status

from core.auth import pwd_context
from dal import Database
from dal.database.DatabaseAuthService import UserAlreadyExistsError
from rest.Authentication.entity import TokenResponse, UserRegistrationForm

security = HTTPBasic()

class Authentication:

    def __init__(self):
        self.router = APIRouter(prefix="/user", tags=["Authentication"])

        # self.router.add_api_route(
        #     "/token",
        #     self.token,
        #     methods=["POST"],
        #     response_model=TokenResponse,
        #     responses={
        #         401: {
        #             "description": "Authentication error",
        #             "content": {
        #                 "application/json": {
        #                     "example": {"detail": "Incorrect username or password"}
        #                 }
        #             }
        #         }
        #     }
        # )

        self.router.add_api_route(
            "/registration",
            self.registration,
            methods=["POST"],
            response_model=TokenResponse,
            responses={
                409: {
                    "description": "User already exists",
                    "content": {"application/json": {"example": {"detail": "Already registered"}}},
                },
                500: {
                    "description": "Unexpected error",
                    "content": {"application/json": {"example": {"detail": "Error register User."}}},
                },
            }
        )

    # @staticmethod
    # async def token(credentials: HTTPBasicCredentials = Depends(security)):
    #     await BasicAuth.auth(credentials.username, credentials.password)
    #
    #     return TokenResponse(
    #         access_token=BasicAuth.create_token(credentials.username, credentials.password),
    #         token_type="basic",
    #     )


    @staticmethod
    async def registration(form_data: UserRegistrationForm) -> int:
        try:
            user = await Database.AuthService.register_user(
                login=form_data.login,
                hashed_password=pwd_context.hash(form_data.password)
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

        return 200


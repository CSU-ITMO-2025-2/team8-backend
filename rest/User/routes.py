from typing import Annotated

from fastapi import HTTPException, status
from fastapi.params import Depends
from sqlalchemy import CursorResult

from app.db.DAO import DAO
from app.db.schema import User as UserSchema
from app.jwt_auth.auth_jwt import get_current_active_user
from app.rest.Admin.entity import UserDetailsResponse, UsersResponse
from app.rest.CustomAPIRouter import APIRouter
from app.rest.Transaction.entity import TransactionResponse
from app.rest.User.entity import UserProfileResponse, User as UserModel, UserResponse, UserProfileUpdateRequest, \
    UserProfileUpdateResponse
from app.rest.User.handler import update_user_profile, get_user_profile, delete_user


class User:
    def __init__(self):
        self.route = APIRouter(prefix="/user", tags=["User"])
        self.route.add_api_route("/", self.read_users_me, methods=["GET"], response_model=UserResponse,
                                 responses={
                                     404: {
                                         "description": "UserNotFound",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "User not found"
                                                     }
                                                 }
                                             }
                                     }
                                 }
                                 )
        self.route.add_api_route("/profile", self.read_user_profile_me, methods=["GET"],
                                 response_model=UserProfileResponse,
                                 responses={
                                     404: {
                                         "description": "UserNotFound",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "User not found"
                                                     }
                                                 }
                                             }
                                     }
                                 }
                                 )
        self.route.add_api_route("/profile/update", self.update_profile, methods=["POST"],
                                 responses={
                                     200: {
                                         "description": "SuccessUpdateProfile",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": 200
                                                 }
                                             }
                                     },
                                     500: {
                                         "description": "FailedUpdateProfile",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Can't update profile"
                                                     }
                                                 }
                                             }
                                     }

                                 })
        self.route.add_api_route("/delete", self.delete_user, methods=["GET"],
                                 responses={
                                     200: {
                                         "description": "SuccessDeleteUser",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": 200
                                                 }
                                             }
                                     },
                                     500: {
                                         "description": "FailedDeleteUser",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Can't delete user"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route('/web_me', self.web_me, methods=['GET'], response_model=UserDetailsResponse)

    @staticmethod
    async def read_users_me(current_user: Annotated[UserSchema, Depends(get_current_active_user)]):
        return UserResponse(id=current_user.id, email=current_user.email, created_at=current_user.created_at, name=current_user.profile.name, balance=current_user.balance.voice_seconds, role=current_user.role)

    @staticmethod
    async def web_me(current_user: Annotated[UserSchema, Depends(get_current_active_user)]):
        user = UsersResponse(id=current_user.id, email=current_user.email, created_at=current_user.created_at,
                             name=current_user.profile.name,
                             balance=current_user.balance.voice_seconds, role=current_user.role)
        transactions = await DAO().Transaction.get(current_user.id)
        response = [TransactionResponse(**transaction.__dict__) for transaction in transactions]
        if user:
            return UserDetailsResponse(**user.model_dump(), transactions=response)


    @staticmethod
    async def update_profile(current_user: Annotated[UserSchema, Depends(get_current_active_user)],
                             update_fields: UserProfileUpdateRequest
                             ) -> UserProfileUpdateResponse:
        result = await update_user_profile(user_id=current_user.id, **dict(update_fields))
        if result:
            return UserProfileUpdateResponse(detail="Profile updated")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Can't update profile",
        )

    @staticmethod
    async def read_user_profile_me(current_user: Annotated[UserSchema, Depends(get_current_active_user)]):
        user_profile = await get_user_profile(current_user.id)
        if user_profile:
            return user_profile
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile not found!",
        )

    @staticmethod
    async def delete_user(current_user: Annotated[UserSchema, Depends(get_current_active_user)]):
        if isinstance(await delete_user(user_id=current_user.id), CursorResult):
            return status.HTTP_200_OK
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cant delete user",
            )

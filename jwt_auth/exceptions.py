from fastapi import HTTPException, status


class AuthJWTException(Exception):
    """
    Base except which all fastapi_jwt_auth errors extend
    """


class AuthenticateUserError(AuthJWTException, HTTPException):
    """
    An error authenticating user
    """

    def __init__(self, status_code: int, detail: str):
        super(HTTPException, self).__init__(status_code=status_code, detail=detail)


class ValidateCredentialsError(AuthJWTException, HTTPException):
    """
    An error validating credentials
    """

    def __init__(self, status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"):
        super(HTTPException, self).__init__(status_code=status_code, detail=detail)


class UserNotFound(AuthJWTException, HTTPException):
    """
    An error authenticating user
    """

    def __init__(self, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile not found!"):
        super(HTTPException, self).__init__(status_code=status_code, detail=detail)

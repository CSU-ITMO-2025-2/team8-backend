from typing import Callable

from passlib.context import CryptContext

from .config import LoadConfig


class AuthConfig:
    _secret_key = None
    _tg_secret_key = None
    _pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _algorithm = "HS256"
    _access_token_expires = None
    _reset_token_expires = None
    # _refresh_token_expires = None

    @classmethod
    def load_config(cls, settings: [..., Callable]):
        try:
            config = LoadConfig(**settings())

            cls._secret_key = config.authjwt_secret_key
            cls._algorithm = config.authjwt_algorithm
            cls._access_token_expires = config.authjwt_access_token_expires
            cls._reset_token_expires = config.authjwt_reset_token_expires
            cls._tg_secret_key = config.tg_authjwt_secret_key
            # cls._refresh_token_expires = config.authjwt_refresh_token_expires
        except Exception as e:
            print("Error loading config: ", e)
            raise e



from datetime import timedelta

from pydantic import BaseModel, StrictStr, StrictInt, StrictBool, ConfigDict


class LoadConfig(BaseModel):
    authjwt_secret_key: StrictStr | None = None
    tg_authjwt_secret_key: StrictStr | None = None
    authjwt_algorithm: StrictStr | None = "HS256"
    authjwt_access_token_expires: StrictBool | StrictInt | timedelta | None = timedelta(minutes=600)
    authjwt_reset_token_expires: StrictBool | StrictInt | timedelta | None = timedelta(minutes=5)
    # authjwt_refresh_token_expires: StrictBool | StrictInt | timedelta | None = timedelta(days=30)
    model_config = ConfigDict(str_min_length=1, str_strip_whitespace=True)

from pydantic import BaseModel

from app.db.schema.Base import LanguageCode


class Text(BaseModel):
    language_code: LanguageCode
    text: str

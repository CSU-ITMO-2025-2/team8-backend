from typing import Optional

from starlette import status

from dal import DAO


async def post_session(session_key: str, user_agent: str):
    result = await DAO().UserSession.post(session_key, user_agent)
    if len(result.inserted_primary_key):
        return False
    return True


async def get_user(email: str = None, user_id: str = None, telegram_id: int = None) -> Optional[User]:
    result = await DAO().User.get(email, user_id, telegram_id)
    if result:
        return result
    return None


async def set_telegram_id(user_id: str, telegram_id: int):
    result = await DAO().User.set_telegram_id(user_id, telegram_id)
    if result.rowcount == 0:
        return False
    return True


async def registration_user(email, password, telegram_id, session_key, name):
    return await DAO().User.post(email=email, password=password, telegram_id=telegram_id,
                                 session_key=session_key, name=name)


async def create_confirm_code(user_id: str, code: int, type_code: TokenType):
    result = await DAO().Confirm.post(user_id, code, type_code)
    if len(result.inserted_primary_key) == 0:
        return False
    return True


async def get_confirm_code(token_type: TokenType, user_id: str):
    return await DAO().Confirm.get(token_type, user_id)


async def confirm_code(user_id: str):
    return await DAO().User.update_confirm_email(user_id)


async def change_password(user_id: str, password: str):
    result = await DAO().User.update_password(user_id, password)
    if result.rowcount == 0:
        return False
    return True

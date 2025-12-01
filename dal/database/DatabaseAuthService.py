import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dal.DAO import connection
from dal.schema.Entity.BackendSchema import User


class UserAlreadyExistsError(Exception):
    """Пытаемся создать пользователя с уже занятым логином."""


class InvalidCredentialsError(Exception):
    """Неверная пара логин/пароль."""


class DatabaseAuthService:

    @staticmethod
    @connection
    async def register_user(
        *,
        login: str,
        hashed_password: str,
        session: AsyncSession = None,
    ) -> User:
        """
        Регистрация нового пользователя.

        - кидает UserAlreadyExistsError, если логин уже занят
        - возвращает созданного User
        """

        # Проверяем, что такого логина ещё нет
        stmt = select(User).where(User.login == login)
        existing_user = await session.scalar(stmt)
        if existing_user is not None:
            raise UserAlreadyExistsError(f"User with login {login!r} already exists")

        user = User(
            login=login,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    @connection
    async def get_user(
        *,
        user_id: int | None = None,
        login: str | None = None,
        session: AsyncSession = None,
    ) -> Optional[User]:
        """
        Вернёт пользователя:
          • по user_id, если указан user_id
          • по login, если указан login
          • бросит ValueError, если не передано ни одного параметра
        """

        if user_id is None and login is None:
            raise ValueError("Нужно передать хотя бы user_id или login")

        stmt = select(User)

        if user_id is not None:
            stmt = stmt.where(User.id == user_id)
        if login is not None:
            stmt = stmt.where(User.login == login)

        user: User | None = await session.scalar(stmt)
        return user

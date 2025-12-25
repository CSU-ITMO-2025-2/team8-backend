from asyncio import current_task
from typing import TypeVar

from sqlalchemy.ext.asyncio import create_async_engine, async_scoped_session, async_sessionmaker

from config.settings import Settings

T = TypeVar('T')


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__()
        return cls._instance


class DAO(metaclass=Singleton):

    def __init__(self, url_object=Settings.SQLALCHEMY_DATABASE_URI()):
        self.db_engine = create_async_engine(url_object, pool_recycle=3, pool_pre_ping=True)
        self.Session = async_scoped_session(async_sessionmaker(bind=self.db_engine, expire_on_commit=False),
                                            current_task)
        print("DAO initialized")


def connection(method):
    async def wrapper(*args, **kwargs):
        async with DAO().Session() as session:
            try:
                kwargs["session"] = session
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(*args, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем сессию при ошибке
                raise e  # Поднимаем исключение дальше
            finally:
                await session.close()  # Закрываем сессию

    return wrapper

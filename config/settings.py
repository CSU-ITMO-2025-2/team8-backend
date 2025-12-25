import enum
import functools
import os
from pathlib import Path
from typing import Dict, Any, Set

import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class KafkaTopics(enum.Enum):
    ACTIVE_TASKS = 'active_tasks'
    DLQ_TASKS = 'dlq_tasks'
    COMPLETED_TASKS = 'completed_tasks'
    ANALYTICS_TASKS = 'analytics_tasks'


class _LoadConfig(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_DRIVER_NAME: str

    KAFKA_SERVERS: str

    # AM_IN_DOCKER_COMPOSE: bool = False

    EXTRA_PARAMS: Dict[str, Any] = {}  # Словарь для хранения дополнительных параметров

    def __init__(self, **values):
        super().__init__(**values)
        self._load_extra_params()


    # @model_validator(mode='after')
    # def check_in_docker_compose(self) -> Self:
    #     if self.AM_IN_DOCKER_COMPOSE:
    #         self.DB_HOST = 'postgres_container'
    #     return self

    def _load_extra_params(self):
        """
        Загрузка EXTRA параметров из .env файла
        Если параметра нет в объекте, он добавляется в словарь EXTRA_PARAMS
        """

        _env_file = self.model_config.get('env_file')
        defined_field_names: Set[str] = set(self.model_fields.keys())

        if _env_file and os.path.exists(_env_file):
            env_vars_from_file = dotenv.dotenv_values(_env_file)

            for key, value in env_vars_from_file.items():
                if key not in defined_field_names:
                    self.EXTRA_PARAMS[key] = value

    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parent / ".env"), extra='ignore')


class Settings:
    __DB_HOST: str
    __DB_PORT: int
    __DB_USER: str
    __DB_PASSWORD: str
    __DB_NAME: str
    __DB_DRIVER_NAME: str

    __KAFKA_SERVERS: str

    __loaded: bool = False

    @classmethod
    def __load__(cls):
        settings = _LoadConfig()
        cls.__DB_HOST = settings.DB_HOST
        cls.__DB_PORT = settings.DB_PORT
        cls.__DB_USER = settings.DB_USER
        cls.__DB_PASSWORD = settings.DB_PASSWORD
        cls.__DB_NAME = settings.DB_NAME
        cls.__DB_DRIVER_NAME = settings.DB_DRIVER_NAME

        cls.__KAFKA_SERVERS = settings.KAFKA_SERVERS

        cls.__EXTRA_PARAMS = settings.EXTRA_PARAMS


        cls.__loaded = True

    @staticmethod
    def __check_loaded(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not Settings.__loaded:
                Settings.__load__()
            return func(*args, **kwargs)

        return wrapper

    @classmethod
    @__check_loaded
    def SQLALCHEMY_DATABASE_URI(cls) -> URL:
        return URL.create(
            drivername=cls.__DB_DRIVER_NAME,
            username=cls.__DB_USER,
            password=cls.__DB_PASSWORD,
            host=cls.__DB_HOST,
            port=cls.__DB_PORT,
            database=cls.__DB_NAME
        )

    @classmethod
    @__check_loaded
    def KAFKA_SERVERS(cls) -> str:
        return cls.__KAFKA_SERVERS


    @classmethod
    @__check_loaded
    def EXTRA_PARAMS(cls) -> dict:
        return cls.__EXTRA_PARAMS



if __name__ == '__main__':
    print(Settings.EXTRA_PARAMS())
    pass

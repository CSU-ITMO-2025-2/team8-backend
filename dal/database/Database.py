import asyncio
import inspect
import os
from pathlib import Path
from urllib.parse import quote_plus

from alembic import command, context
from alembic.autogenerate import compare_metadata
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

import alembic.config
from sqlalchemy import URL, engine_from_config, pool, create_engine, Connection

from .DatabaseIngestionService import DatabaseIngestionService
from .IngestionCursorService import IngestionCursorService
from .TaskPersistenceService import TaskPersistenceService
from ..DAO import DAO
from ..schema import Base

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Явно устанавливаем уровень логирования для alembic (если необходимо)
logging.getLogger('alembic').setLevel(logging.DEBUG)

class Database:
    IngestionService = DatabaseIngestionService()
    CursorService = IngestionCursorService()
    TaskPersistence = TaskPersistenceService()

    @classmethod
    async def checkDatabase(cls):
        # class_path = inspect.getmodule(cls).__file__
        # print("Class path:", class_path)
        # # Получаем директорию, убирая имя файла
        # directory_path = Path(class_path).parent.parent
        # # Формируем полный путь к конфигурационному файлу
        # config_path = directory_path / 'alembic.ini'
        config_path = Path(Path.cwd(), 'alembic.ini')
        alembic_config = alembic.config.Config(config_path)
        script = ScriptDirectory.from_config(alembic_config)
        env_context = EnvironmentContext(
            alembic_config,
            script,
            as_sql=False,
        )

        async with DAO().db_engine.connect() as conn:
            def get_diff(connection):
                env_context.configure(connection=connection, target_metadata=Base.metadata)
                return compare_metadata(env_context.get_context(), Base.metadata)

            diff = await conn.run_sync(get_diff)

        if diff:
            raise Exception(f"Database has been changed, please run auto migration. {diff}")




import asyncio
from pathlib import Path

import alembic
from alembic import command
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

from dal import Database
from dal.schema import User, Role


async def testDAL() -> None:
    await Database.checkDatabase()

    await Database.User.post(User(telegram_id=1213, role=Role.USER), session=None)
    user = await Database.User.get(telegram_id=1213)
    pass

if __name__ == "__main__":
    asyncio.run(testDAL())


# async def main():
#     config_path = Path(Path.cwd(), 'alembic.ini')
#     alembic_config = alembic.config.Config(config_path)
#     command.revision(alembic_config, autogenerate=True)
#     command.upgrade(alembic_config, 'head')
# if __name__ == '__main__':
#     asyncio.run(main())
from .DatabaseAuthService import DatabaseAuthService


import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Явно устанавливаем уровень логирования для alembic (если необходимо)
logging.getLogger('alembic').setLevel(logging.DEBUG)

class Database:
    AuthService = DatabaseAuthService()

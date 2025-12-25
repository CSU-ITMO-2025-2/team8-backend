from .DatabaseAuthService import DatabaseAuthService


import logging

from .DatabaseChatService import DatabaseChatService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Явно устанавливаем уровень логирования для alembic (если необходимо)
logging.getLogger('alembic').setLevel(logging.DEBUG)

class Database:
    AuthService = DatabaseAuthService()
    ChatService = DatabaseChatService()

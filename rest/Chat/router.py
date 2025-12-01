# api/chat.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import BasicAuth
from dal import Database
from dal.database.DatabaseChatService import ChatSessionNotFound
from dal.schema.Entity.BackendSchema import User
from rest.Chat.schemas import (
    ChatSessionCreate,
    ChatSessionRead,
    ChatSessionWithMessages,
    ChatSessionListItem,
    MessageCreate,
    MessageRead,
    MessageRole,
)


class ChatAPI:
    def __init__(self):
        self.router = APIRouter(prefix="/chat", tags=["Chat"])

        # Создание новой сессии чата
        self.router.add_api_route(
            "/sessions",
            self.create_session,
            methods=["POST"],
            response_model=ChatSessionWithMessages,
            status_code=status.HTTP_201_CREATED,
        )

        # Список сессий пользователя
        self.router.add_api_route(
            "/sessions",
            self.list_sessions,
            methods=["GET"],
            response_model=List[ChatSessionListItem],
        )

        # Получение одной сессии с сообщениями
        self.router.add_api_route(
            "/sessions/{session_id}",
            self.get_session,
            methods=["GET"],
            response_model=ChatSessionWithMessages,
        )

        # Отправка сообщения в сессию
        self.router.add_api_route(
            "/sessions/{session_id}/messages",
            self.send_message,
            methods=["POST"],
            response_model=MessageRead,
            status_code=status.HTTP_201_CREATED,
        )

    @staticmethod
    async def create_session(
        data: ChatSessionCreate,
        current_user: User = Depends(BasicAuth.token_auth),
    ) -> ChatSessionWithMessages:
        session = await Database.ChatService.create_session(
            user_id=current_user.id,
            data=data,
        )
        session_full = await Database.ChatService.get_session_for_user(
            session_id=session.id,
            user_id=current_user.id,
            with_messages=True,
        )
        if session_full is None:
            raise HTTPException(status_code=500, detail="Session not found after create")

        return session_full

    @staticmethod
    async def list_sessions(
        limit: int = 20,
        offset: int = 0,
        current_user: User = Depends(BasicAuth.token_auth),
    ) -> List[ChatSessionListItem]:
        sessions = await Database.ChatService.get_user_sessions(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )

        return sessions

    @staticmethod
    async def get_session(
        session_id: int,
        current_user: User = Depends(BasicAuth.token_auth),
    ) -> ChatSessionWithMessages:
        session = await Database.ChatService.get_session_for_user(
            session_id=session_id,
            user_id=current_user.id,
            with_messages=True,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
        return session

    @staticmethod
    async def send_message(
        session_id: int,
        data: MessageCreate,
        current_user: User = Depends(BasicAuth.token_auth),
    ) -> MessageRead:
        session = await Database.ChatService.get_session_for_user(
            session_id=session_id,
            user_id=current_user.id,
            with_messages=False,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

        # Для пользовательского эндпоинта обычно форсим роль = user
        role = MessageRole.user

        try:
            msg = await Database.ChatService.create_message(
                session_id=session.id,
                user_id=current_user.id,
                role=role,
                content=data.content,
                meta=data.meta,
            )
            return msg
        except ChatSessionNotFound:
            raise HTTPException(status_code=404, detail="Chat session not found")

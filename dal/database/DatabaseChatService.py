from typing import Optional, Dict, Any, List

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dal.DAO import connection
from dal.schema.Entity.BackendSchema import ChatSession, Message
from rest.Chat.schemas import ChatSessionCreate, MessageCreate, MessageRole

class ChatSessionNotFound(Exception):
    pass

class DatabaseChatService:
    @staticmethod
    @connection
    async def create_session(
        user_id: int,
        data: ChatSessionCreate,
        session: AsyncSession = None,
    ) -> ChatSession:
        chat_session = ChatSession(
            user_id=user_id,
            title=data.title,
            model_name=data.model_name or "gemma-3",
            temperature=data.temperature if data.temperature is not None else 0.7,
            max_tokens=data.max_tokens if data.max_tokens is not None else 1024,
            extra_params=data.extra_params,
        )
        session.add(chat_session)
        await session.flush()

        if data.first_message is not None:
            msg_data: MessageCreate = data.first_message
            msg = Message(
                session_id=chat_session.id,
                role=msg_data.role,
                content=msg_data.content,
                meta=msg_data.meta,
            )
            session.add(msg)

        await session.commit()
        await session.refresh(chat_session)
        return chat_session

    @staticmethod
    @connection
    async def get_user_sessions(
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        session: AsyncSession = None,
    ) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .where(ChatSession.is_archived == False)  # noqa: E712
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    @connection
    async def get_session_for_user(
        session_id: int,
        user_id: int,
        with_messages: bool = False,
        session: AsyncSession = None,
    ) -> Optional[ChatSession]:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )

        if with_messages:
            stmt = stmt.options(selectinload(ChatSession.messages))

        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    @connection
    async def create_message(
        *,
        session_id: int,
        user_id: int,
        role: MessageRole,
        content: str,
        meta: Optional[Dict[str, Any]] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        latency_ms: Optional[int] = None,
        session: AsyncSession = None,
    ) -> Message:
        # Проверяем, что сессия пользователя существует (по желанию)
        # можно убрать этот select, если проверяешь в хэндлере
        chat_session = await session.get(ChatSession, session_id)
        if chat_session is None:
            # тут лучше своё исключение бросить, а в ручке перевести в 404
            raise ValueError("ChatSession not found")

        if chat_session.user_id != user_id:
            raise ChatSessionNotFound()

        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            meta=meta,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )
        session.add(msg)

        await session.commit()
        await session.refresh(msg)
        return msg

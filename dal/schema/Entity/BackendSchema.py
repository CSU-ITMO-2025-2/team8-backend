from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
    Enum,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------- ENUM'ы ----------

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"  # на будущее, если будут функции/инструменты


# ---------- МОДЕЛИ ----------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # просто логин вместо почты
    login: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # хэш пароля (bcrypt/argon2 и т.п.)
    hashed_password: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} login={self.login!r}>"


class ChatSession(Base):
    """
    Один диалог (тред) между пользователем и AI.
    """

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Короткий заголовок/название чата (можно генерить автоматически)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Параметры модели, с которой ведётся чат (даже если у тебя одна модель, пригодится)
    model_name: Mapped[str] = mapped_column(String(100), default="gemma-3")
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(default=1024)
    extra_params: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id}>"


class Message(Base):
    """
    Сообщения внутри чата. Сохраняем как от пользователя, так и от ассистента.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)

    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), index=True)
    content: Mapped[str] = mapped_column(Text)

    # Для ассистентских сообщений можно хранить токены, время ответа и т.п.
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Любые дополнительные данные: сырой ответ модели, http-пэйлоады и т.д.
    metadata: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, default=True
    )  # мягкое удаление/скрытие

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} session_id={self.session_id} "
            f"role={self.role.value}>"
        )


# Индексы для ускорения выборок
Index("ix_messages_session_created", Message.session_id, Message.created_at)
Index("ix_sessions_user_created", ChatSession.user_id, ChatSession.created_at)

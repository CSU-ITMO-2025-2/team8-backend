from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ---------- Message ----------

class MessageBase(BaseModel):
    role: MessageRole
    content: str


class MessageCreate(BaseModel):
    content: str
    role: MessageRole = MessageRole.user
    meta: Optional[Dict[str, Any]] = None


class MessageRead(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None
    is_visible: bool

    class Config:
        from_attributes = True


# ---------- ChatSession ----------

class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extra_params: Optional[Dict[str, Any]] = None


class ChatSessionCreate(ChatSessionBase):
    """
    Создание сессии чата:
    - можно передать настройки модели
    - можно сразу передать первое сообщение пользователя
    """
    first_message: Optional[MessageCreate] = None


class ChatSessionRead(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_archived: bool

    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSessionRead):
    """
    Для эндпоинта получения чата вместе с сообщениями.
    """
    messages: List[MessageRead] = []


class ChatSessionListItem(BaseModel):
    id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    last_message: Optional[MessageRead] = None

    class Config:
        from_attributes = True

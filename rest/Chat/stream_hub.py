import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel, Field


class StreamState(BaseModel):
    request_id: str
    session_id: int
    user_id: int

    text: str = ""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[int] = None

    meta: Dict[str, Any] = Field(default_factory=dict)
    is_done: bool = False

    class Config:
        arbitrary_types_allowed = True


class SingletonMeta(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class StreamHub(metaclass=SingletonMeta):
    def __init__(self):
        self._lock = asyncio.Lock()
        self._subs: Dict[str, List[asyncio.Queue]] = {}
        self._state: Dict[str, StreamState] = {}

    async def register(self, request_id: str, session_id: int, user_id: int) -> None:
        async with self._lock:
            self._state[request_id] = StreamState(
                request_id=request_id,
                session_id=session_id,
                user_id=user_id,
            )

    async def get_state(self, request_id: str) -> Optional[StreamState]:
        async with self._lock:
            return self._state.get(request_id)

    async def subscribe(self, request_id: str) -> AsyncIterator[dict]:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subs.setdefault(request_id, []).append(q)

        try:
            while True:
                event = await q.get()
                yield event
                if event.get("type") == "done":
                    break
        finally:
            async with self._lock:
                subs = self._subs.get(request_id, [])
                if q in subs:
                    subs.remove(q)
                if not subs:
                    self._subs.pop(request_id, None)

    async def publish(self, request_id: str, event: dict) -> None:
        async with self._lock:
            subs = list(self._subs.get(request_id, []))
        for q in subs:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # клиент не читает — дропаем
                pass

    async def mark_done(self, request_id: str) -> None:
        async with self._lock:
            st = self._state.get(request_id)
            if st:
                st.is_done = True
        await self.publish(request_id, {"type": "done"})

    async def append_text(self, request_id: str, delta: str) -> None:
        async with self._lock:
            st = self._state.get(request_id)
            if st:
                st.text += delta

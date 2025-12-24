# rest/Chat/kafka_stream_consumer.py
from logging import Logger
from typing import Any, Dict, Optional

from core.consumer import ConsumerBase
from core.llm_schemas import LlmStreamChunk
from dal.schema.Entity.BackendSchema import MessageRole
from rest.Chat.stream_hub import StreamHub

from dal.database import Database


class KafkaLlmStreamConsumer(ConsumerBase):
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        logger: Logger,
        value_deserializer,
        hub: StreamHub,
        database: Database,
        **kwargs,
    ):
        super().__init__(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id=group_id,
            logger=logger,
            value_deserializer=value_deserializer,
            enable_auto_commit=True,
            auto_offset_reset="latest",
            **kwargs,
        )
        self._hub = hub
        self._Database = database

    async def run_forever(self):
        async for msg in self:
            try:
                data: LlmStreamChunk = msg.value  # pydantic

                request_id = str(data.request_id)
                if not request_id:
                    continue

                # обычный чанк
                if not data.is_final:
                    delta = data.delta or ""
                    if delta:
                        await self._hub.append_text(request_id, delta)
                        await self._hub.publish(request_id, {"type": "chunk", "delta": delta, "index": data.index})
                    continue

                # финал (is_final=True)
                st = await self._hub.get_state(request_id)
                if st is None:
                    # state потерян — завершим подписчиков, чтобы SSE не висел вечно
                    await self._hub.publish(request_id, {"type": "done"})
                    continue

                # финальный текст: либо воркер пришлёт пустой delta на финале,
                # либо дельта может содержать последний кусок — добавим её в state
                final_delta = data.delta or ""
                if final_delta:
                    await self._hub.append_text(request_id, final_delta)

                final_text = st.text

                # мета: сохраняем полезные поля события
                st.meta.update({
                    "request_id": request_id,
                    "chat_session_id": str(data.chat_session_id) if data.chat_session_id else None,
                    "last_index": data.index,
                    "created_at": data.created_at.isoformat() if getattr(data, "created_at", None) else None,
                })

                # usage может приходить отдельной моделью/полями — обработаем безопасно
                # если у тебя в LlmStreamChunk есть token_usage: TokenUsage | None
                token_usage = getattr(data, "token_usage", None)
                if token_usage is not None:
                    st.prompt_tokens = getattr(token_usage, "prompt_tokens", None)
                    st.completion_tokens = getattr(token_usage, "completion_tokens", None)

                # latency тоже может быть в data.metadata — если есть
                st.latency_ms = getattr(data, "latency_ms", st.latency_ms)

                # 1) финал клиенту
                await self._hub.publish(request_id, {"type": "final", "content": final_text})

                # 2) сохранить в БД (session_id берём из st, он int)
                await self._Database.ChatService.create_message(
                    session_id=st.session_id,
                    role=MessageRole.ASSISTANT,
                    content=final_text,
                    meta=st.meta,
                    prompt_tokens=st.prompt_tokens,
                    completion_tokens=st.completion_tokens,
                    latency_ms=st.latency_ms,
                )

                # 3) закрыть SSE
                await self._hub.mark_done(request_id)

            except Exception:
                self._logger.exception("Error processing LLM stream message")


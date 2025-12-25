from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from core.auth import BasicAuth
from dal import Database
from rest.Chat.stream_hub import StreamHub


def get_hub() -> StreamHub:
    return StreamHub()


class ChatStreamAPI:
    def __init__(self):
        self.router = APIRouter(prefix="/chat", tags=["Chat"])

        self.router.add_api_route(
            "/stream/{request_id}",
            self.stream_by_request_id,
            methods=["GET"],
        )

    @staticmethod
    async def stream_by_request_id(
        request_id: str,
        current_user=Depends(BasicAuth.token_auth),
        hub: StreamHub = Depends(get_hub),
    ):
        st = await hub.get_state(request_id)
        if st is None:
            raise HTTPException(status_code=404, detail="Unknown request_id")

        await Database.ChatService.get_session_for_user(
            session_id=st.session_id,
            user_id=current_user.id,
            with_messages=False,
        )

        async def gen():
            async for event in hub.subscribe(request_id):
                yield {"event": event.get("type", "message"), "data": event}

        return EventSourceResponse(gen())

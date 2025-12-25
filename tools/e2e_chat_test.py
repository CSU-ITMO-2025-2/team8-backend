import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx


def log_pass(msg: str) -> None:
    print(f"PASS: {msg}")

def log_fail(msg: str) -> None:
    print(f"FAIL: {msg}")

def die(msg: str, code: int = 1) -> None:
    log_fail(msg)
    raise SystemExit(code)


def extract_request_id(resp_json: Dict[str, Any]) -> Optional[str]:
    """
    Поддерживаем оба варианта:
    1) { "request_id": "..." }
    2) MessageRead, где request_id лежит в meta: { ..., "meta": { "request_id": "..." } }
    3) { "message": {..., "meta": {"request_id": "..."}}, "request_id": "..." }
    """
    if "request_id" in resp_json and resp_json["request_id"]:
        return str(resp_json["request_id"])

    meta = resp_json.get("meta") or {}
    if isinstance(meta, dict) and meta.get("request_id"):
        return str(meta["request_id"])

    msg = resp_json.get("message")
    if isinstance(msg, dict):
        if msg.get("meta", {}).get("request_id"):
            return str(msg["meta"]["request_id"])
    return None


async def read_sse_until_done(
    client: httpx.AsyncClient,
    url: str,
    timeout_s: float = 120.0
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Читает SSE поток, пока не увидит event/data с type == "done".
    Возвращает (events, final_text).
    """
    events: List[Dict[str, Any]] = []
    final_text = ""
    started = time.time()

    async with client.stream("GET", url, timeout=timeout_s) as r:
        if r.status_code != 200:
            body = await r.aread()
            die(f"SSE GET {url} status={r.status_code} body={body[:400]!r}")

        cur_event_name = None
        cur_data_line = None

        async for line in r.aiter_lines():
            if time.time() - started > timeout_s:
                die(f"SSE timeout after {timeout_s}s")

            if line == "":
                # конец одного SSE сообщения
                if cur_data_line is not None:
                    print(f"SSE GET {url} data={cur_data_line!r}")
                    try:
                        payload = json.loads(cur_data_line)
                    except Exception:
                        payload = {"raw": cur_data_line}

                    if cur_event_name:
                        payload["_event_name"] = cur_event_name

                    events.append(payload)

                    # ожидаемые payload: {"type":"chunk"...} / {"type":"final"...} / {"type":"done"}
                    if payload.get("type") == "final":
                        final_text = payload.get("content", "") or final_text
                    if payload.get("type") == "done":
                        break

                cur_event_name = None
                cur_data_line = None
                continue

            if line.startswith("event:"):
                cur_event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                # в нашем API мы отдаём dict как data -> будет JSON строка
                cur_data_line = line.split(":", 1)[1].strip()

        # если stream оборвался без done — тоже плохо, но иногда прокси режут
        # оставим проверку ниже
    return events, final_text


async def main() -> None:
    base_url = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")
    session_title = os.getenv("SESSION_TITLE", "E2E Test Chat")
    message_text = os.getenv("MESSAGE_TEXT", "Напиши коротенький стих про разработчика и дедлайны (4 строки)")
    sse_timeout = float(os.getenv("SSE_TIMEOUT", "120"))

    headers = {}
    headers["Authorization"] = f"Basic c3RyaW5nOnN0cmluZw=="

    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
        # 1) create session
        r = await client.post("/chat/sessions", json={"title": session_title})
        if r.status_code not in (200, 201):
            die(f"create_session failed status={r.status_code} body={r.text[:400]}")
        sess = r.json()
        session_id = sess.get("id")
        if not session_id:
            die(f"create_session: no id in response: {sess}")
        log_pass(f"create_session id={session_id}")

        # 2) send message
        r = await client.post(f"/chat/sessions/{session_id}/messages", json={"content": message_text, "meta": {"e2e": True}})
        if r.status_code not in (200, 201):
            die(f"send_message failed status={r.status_code} body={r.text[:400]}")
        msg = r.json()
        log_pass(f"send_message saved (status={r.status_code})")

        request_id = extract_request_id(msg)
        if not request_id:
            die(f"send_message: cannot find request_id in response: {msg}")
        log_pass(f"request_id={request_id}")

        # 3) SSE stream
        events, final_text = await read_sse_until_done(client, f"/chat/stream/{request_id}", timeout_s=sse_timeout)

        types = [e.get("_event_name") for e in events if isinstance(e, dict)]
        if "chunk" not in types and "final" not in types:
            die(f"SSE: no chunk/final events received. types={types} events_sample={events[:3]}")

        if "done" not in types:
            die(f"SSE: did not receive done. types={types}")

        log_pass(f"SSE received events={len(events)} (types={sorted(set([t for t in types if t]))})")

        if final_text:
            log_pass(f"SSE final_text_len={len(final_text)}")
        else:
            # не всегда обязательно, но обычно должен быть
            log_fail("SSE final text is empty (might be ok if your worker uses only chunks)")

        # 4) verify persisted assistant message exists via API
        r = await client.get(f"/chat/sessions/{session_id}")
        if r.status_code != 200:
            die(f"get_session failed status={r.status_code} body={r.text[:400]}")
        sess_full = r.json()
        messages = sess_full.get("messages") or []

        has_user = any(m.get("role") == "user" and m.get("content") == message_text for m in messages if isinstance(m, dict))
        has_assistant = any(m.get("role") == "assistant" and (m.get("content") or "") for m in messages if isinstance(m, dict))

        if not has_user:
            die("DB check via API: user message not found in session messages")
        log_pass("DB check via API: user message present")

        if not has_assistant:
            die("DB check via API: assistant message not found/persisted yet")
        log_pass("DB check via API: assistant message present")

        log_pass("E2E chain OK ✅")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)

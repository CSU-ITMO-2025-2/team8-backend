import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, get_redoc_html

from config.settings import Settings
from core.llm_schemas import LlmStreamChunk
from core.producer import LlmKafkaProducer
from rest.Authentication.router import Authentication
from rest.Chat.kafka_stream_consumer import KafkaLlmStreamConsumer
from rest.Chat.router import ChatAPI
from rest.Chat.stream_hub import StreamHub
from rest.Chat.stream_router import ChatStreamAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # singletons / state
    app.state.hub = StreamHub()

    producer = LlmKafkaProducer()
    await producer.start()
    app.state.producer = producer

    consumer = KafkaLlmStreamConsumer(
        bootstrap_servers=Settings.KAFKA_SERVERS(),
        topic="llm.chat.token",
        group_id="backend-stream",
        logger=app.logger if hasattr(app, "logger") else __import__("logging").getLogger("app"),
        value_deserializer=LlmStreamChunk.model_validate_json,
        hub=app.state.hub,
        database=__import__("dal").Database,   # или передай напрямую
    )
    await consumer.start()
    consumer_task = __import__("asyncio").create_task(consumer.run_forever())
    app.state.stream_consumer = consumer
    app.state.stream_consumer_task = consumer_task

    try:
        yield
    finally:
        # shutdown
        consumer_task.cancel()
        try:
            await consumer_task
        except Exception:
            pass
        await consumer.stop()
        await producer.stop()


app = FastAPI(title="team-8", version="0.1", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@next/bundles/redoc.standalone.js",
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(Authentication().router)
app.include_router(ChatAPI().router)
app.include_router(ChatStreamAPI().router)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)

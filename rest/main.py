import os
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, get_redoc_html

from app.jwt_auth import AuthJWT
from app.rest.Admin.route import Admin
from app.rest.Authentication.route import Authentication
from app.rest.ConfrimEmail.route import ConfirmEmail
from app.rest.Dialogue.route import Dialogue
from app.rest.Message.route import Message, RabbitMQManager
from app.rest.ResetPassword.route import ResetPassword
from app.rest.Transaction.route import Transaction
from app.rest.User.routes import User


@AuthJWT.load_config
def get_config():
    from json import loads
    with open("jwt_auth/config.json", 'r') as f:
        config_data = loads(f.read())
    config_data["authjwt_secret_key"] = "NEW_SECRET_KEY"
    return config_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    Message.rabbitmq_manager = RabbitMQManager(rabbitmq_host=host, rabbitmq_port=5672)
    await Message.rabbitmq_manager.connect()
    yield
    # Clean up the ML models and release the resources
    await Message.rabbitmq_manager.close()


app = FastAPI(title="Talktut", version="0.1", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
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


app.include_router(Authentication().route)
app.include_router(ResetPassword().route)
app.include_router(ConfirmEmail().route)
app.include_router(User().route)
app.include_router(Dialogue().route)
app.include_router(Transaction().route)
app.include_router(Message().route)
app.include_router(Admin().route)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)

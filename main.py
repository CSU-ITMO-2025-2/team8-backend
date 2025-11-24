import asyncio
import logging

import uvicorn

from .dal import DAO


async def main() -> None:
    await DAO().checkDatabase()
    from app.rest.main import app
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, reload=False)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

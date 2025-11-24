from typing import Any

from fastapi import APIRouter as FastAPIRouter


class APIRouter(FastAPIRouter):

    def add_api_route(
            self, path: str, endpoint, *, include_in_schema: bool = True, **kwargs: Any
    ) -> None:
        if path.endswith("/"):
            path = path[:-1]

        super().add_api_route(
            path, endpoint=endpoint, include_in_schema=include_in_schema, **kwargs
        )

        alternate_path = path + "/"
        super().add_api_route(
            alternate_path, endpoint=endpoint, include_in_schema=False, **kwargs
        )

from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class SinglePageApplicationFiles(StaticFiles):
    """Serve the React entry point for client-side routes in production."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 404 and "." not in path.rsplit("/", 1)[-1]:
            return await super().get_response("index.html", scope)
        return response

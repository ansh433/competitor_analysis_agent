import asyncio

import httpx
from fastapi import FastAPI


class IntegrationClient:
    """Synchronous facade over HTTPX's in-process ASGI transport."""

    def __init__(self, application: FastAPI) -> None:
        self._application = application

    def get(self, path: str, *, headers: dict[str, str] | None = None) -> httpx.Response:
        return self.request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        *,
        json: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("POST", path, json=json, headers=headers)

    def put(
        self,
        path: str,
        *,
        json: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("PUT", path, json=json, headers=headers)

    def patch(
        self,
        path: str,
        *,
        json: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("PATCH", path, json=json, headers=headers)

    def delete(
        self,
        path: str,
        *,
        json: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("DELETE", path, json=json, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=self._application)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, json=json, headers=headers)

        return asyncio.run(send())

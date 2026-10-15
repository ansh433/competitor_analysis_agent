from datetime import datetime
from typing import Literal

from tavily import TavilyClient

from app.core.errors import ExternalProviderError
from app.providers.base import SearchHit, SearchResponse


class TavilySearchProvider:
    def __init__(self, api_key: str) -> None:
        self._client = TavilyClient(api_key=api_key)

    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        include_domains: list[str] | None = None,
        topic: str = "general",
    ) -> SearchResponse:
        tavily_topic: Literal["general", "news"] = "news" if topic == "news" else "general"
        try:
            response = self._client.search(
                query=query,
                search_depth="advanced",
                topic=tavily_topic,
                max_results=maximum_results,
                include_answer=False,
                include_raw_content=False,
                include_images=False,
                include_domains=include_domains,
            )
        except Exception as error:
            raise ExternalProviderError("Company source search failed") from error

        results: list[SearchHit] = []
        for item in response.get("results", []):
            if not isinstance(item, dict):
                continue
            published_at = None
            published_date = item.get("published_date")
            if isinstance(published_date, str):
                try:
                    published_at = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                except ValueError:
                    published_at = None
            results.append(
                SearchHit(
                    title=str(item.get("title") or "Untitled source"),
                    url=str(item.get("url") or ""),
                    snippet=str(item.get("content") or ""),
                    score=max(0.0, min(float(item.get("score") or 0), 1.0)),
                    published_at=published_at,
                )
            )
        return SearchResponse(query=query, results=[result for result in results if result.url])


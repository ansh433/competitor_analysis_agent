from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeVar

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str
    score: float = Field(ge=0, le=1)
    published_at: datetime | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHit]


class RetrievedPage(BaseModel):
    url: str
    title: str
    content: str
    retrieved_at: datetime
    publisher: str
    content_type: str


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class SearchProvider(Protocol):
    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        include_domains: list[str] | None = None,
        topic: str = "general",
    ) -> SearchResponse: ...


class PageFetcher(Protocol):
    def fetch(self, url: str) -> RetrievedPage: ...


class ModelProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    def generate_text(self, system_prompt: str, user_prompt: str) -> str: ...

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[ResponseModel],
    ) -> ResponseModel: ...


@dataclass(frozen=True)
class ResearchProviders:
    search: SearchProvider
    pages: PageFetcher
    model: ModelProvider


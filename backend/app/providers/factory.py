from app.core.config import Settings
from app.core.errors import ExternalProviderError
from app.providers.base import ResearchProviders
from app.providers.deterministic import (
    DeterministicModelProvider,
    DeterministicPageFetcher,
    DeterministicSearchProvider,
)
from app.providers.gemini import GoogleGeminiModelProvider
from app.providers.safe_fetch import SafeHttpPageFetcher
from app.providers.tavily_search import TavilySearchProvider


def build_research_providers(settings: Settings, upgraded_model: bool = False) -> ResearchProviders:
    if settings.provider_mode == "deterministic":
        return ResearchProviders(
            search=DeterministicSearchProvider(),
            pages=DeterministicPageFetcher(),
            model=DeterministicModelProvider(),
        )
    if not settings.tavily_api_key or not settings.gemini_api_keys:
        raise ExternalProviderError("Live research requires Gemini and Tavily API keys")
    model_name = settings.upgraded_gemini_model if upgraded_model else settings.gemini_model
    return ResearchProviders(
        search=TavilySearchProvider(settings.tavily_api_key.get_secret_value()),
        pages=SafeHttpPageFetcher(
            timeout_seconds=settings.request_timeout_seconds,
            maximum_bytes=settings.maximum_fetched_bytes,
        ),
        model=GoogleGeminiModelProvider(
            model_name=model_name,
            api_keys=settings.gemini_api_keys,
        ),
    )

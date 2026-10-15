from datetime import UTC, datetime
from urllib.parse import quote_plus, urlsplit

from app.providers.base import ResponseModel, RetrievedPage, SearchHit, SearchResponse


class DeterministicSearchProvider:
    """Predictable provider used by local integration tests and demos."""

    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        include_domains: list[str] | None = None,
        topic: str = "general",
    ) -> SearchResponse:
        slug = quote_plus(query.lower())[:50]
        domains = include_domains or ["example.com", "news.example.com", "docs.example.com"]
        results = [
            SearchHit(
                title=f"{query} — official company overview",
                url=f"https://{domains[0]}/companies/{slug}",
                snippet=f"Official overview, products, customers, and positioning for {query}.",
                score=0.96,
            ),
            SearchHit(
                title=f"{query} pricing and plans",
                url=f"https://{domains[min(1, len(domains) - 1)]}/pricing/{slug}",
                snippet=f"Published pricing and plan information for {query}.",
                score=0.91,
            ),
            SearchHit(
                title=f"{query} product announcement",
                url=f"https://{domains[min(2, len(domains) - 1)]}/news/{slug}",
                snippet=f"A dated product announcement concerning {query}.",
                score=0.84,
                published_at=datetime(2026, 1, 15, tzinfo=UTC),
            ),
        ][:maximum_results]
        return SearchResponse(query=query, results=results)


class DeterministicPageFetcher:
    def fetch(self, url: str) -> RetrievedPage:
        parsed = urlsplit(url)
        title = parsed.path.strip("/").replace("/", " — ").replace("+", " ").title()
        content = (
            f"Published by {parsed.hostname}. This deterministic source describes a collaboration "
            "software company serving product and engineering teams. The public plans are Starter "
            "at no cost, Team at $12 per user each month, and Enterprise with contact-based pricing. "
            "The company emphasizes workflow speed, integrations, and reliable project visibility."
        )
        return RetrievedPage(
            url=url,
            title=title or "Company source",
            content=content,
            retrieved_at=datetime.now(UTC),
            publisher=parsed.hostname or "example.com",
            content_type="text/html",
        )


class DeterministicModelProvider:
    model_name = "deterministic-research-model"

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        del system_prompt
        return (
            "## Deterministic research synthesis\n\n"
            "The available evidence supports a focused comparison. "
            f"Research objective: {user_prompt[:240]}"
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[ResponseModel],
    ) -> ResponseModel:
        del system_prompt, user_prompt
        fixture = deterministic_schema_fixture(schema.__name__)
        return schema.model_validate(fixture)


def deterministic_schema_fixture(schema_name: str) -> dict[str, object]:
    fixtures: dict[str, dict[str, object]] = {
        "ResolvedCompanyIdentity": {
            "canonical_name": "Acme Collaboration",
            "legal_name": "Acme Collaboration, Inc.",
            "website": "https://example.com",
            "domain": "example.com",
            "ambiguities": [],
            "confidence": 0.96,
        },
    }
    return fixtures.get(schema_name, {})


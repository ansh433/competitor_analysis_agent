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
        del system_prompt
        fixture = deterministic_schema_fixture(schema.__name__, user_prompt)
        return schema.model_validate(fixture)


def deterministic_schema_fixture(schema_name: str, prompt: str = "") -> dict[str, object]:
    def fact(value: str | None, urls: list[str] | None = None) -> dict[str, object]:
        return {
            "value": value,
            "classification": "sourced_fact" if value else "unavailable_information",
            "source_urls": urls or (["https://example.com/companies/acme"] if value else []),
        }
    fixtures: dict[str, dict[str, object]] = {
        "ResolvedCompanyIdentity": {
            "canonical_name": "Acme Collaboration",
            "legal_name": "Acme Collaboration, Inc.",
            "website": "https://example.com",
            "domain": "example.com",
            "ambiguities": [],
            "confidence": 0.96,
        },
        "CompanyProfile": {
            "company_name": "Acme Collaboration",
            "legal_name": fact("Acme Collaboration, Inc."),
            "industry": fact("Collaboration software"),
            "headquarters": fact(None),
            "products": ["Project workspace", "Workflow integrations"],
            "target_customers": ["Product teams", "Engineering teams"],
            "positioning": fact("Fast, reliable project visibility"),
            "geographies": [],
            "business_model": fact("Per-user software subscription"),
        },
        "ProductAndPricingProfile": {
            "products": ["Project workspace", "Workflow integrations"],
            "plans": [
                {
                    "name": "Starter",
                    "public_price": "$0",
                    "billing_basis": "per user/month",
                    "included_features": ["Core workspace"],
                    "source_url": "https://example.com/pricing/acme",
                    "classification": "sourced_fact",
                },
                {
                    "name": "Team",
                    "public_price": "$12",
                    "billing_basis": "per user/month",
                    "included_features": ["Integrations", "Advanced workflows"],
                    "source_url": "https://example.com/pricing/acme",
                    "classification": "sourced_fact",
                },
            ],
            "pricing_model": fact("Freemium per-user subscription", ["https://example.com/pricing/acme"]),
            "differentiators": [fact("Workflow speed")],
            "unavailable_information": ["Negotiated enterprise pricing"],
        },
        "CompetitorDiscovery": {
            "candidates": [
                {
                    "name": "Northstar Work",
                    "website": "https://northstar.example.com",
                    "relationship_type": "competitor",
                    "proximity": "direct",
                    "reason": "Targets the same product and engineering teams with project workflows.",
                    "confidence": 0.9,
                    "evidence_urls": ["https://news.example.com/acme-alternatives"],
                },
                {
                    "name": "Taskboard Suite",
                    "website": "https://taskboard.example.com",
                    "relationship_type": "substitute",
                    "proximity": "indirect",
                    "reason": "General work management can replace dedicated product planning workflows.",
                    "confidence": 0.78,
                    "evidence_urls": ["https://docs.example.com/work-management"],
                },
            ],
            "discovery_notes": ["Candidates require normalized product comparison."],
        },
    }
    fixture = fixtures.get(schema_name, {})
    if schema_name == "ResolvedCompanyIdentity" and "northstar" in prompt.lower():
        return {
            **fixture,
            "canonical_name": "Northstar Work",
            "legal_name": "Northstar Work, Inc.",
            "website": "https://northstar.example.com",
            "domain": "northstar.example.com",
        }
    if schema_name == "ResolvedCompanyIdentity" and "taskboard" in prompt.lower():
        return {
            **fixture,
            "canonical_name": "Taskboard Suite",
            "legal_name": "Taskboard Suite, Inc.",
            "website": "https://taskboard.example.com",
            "domain": "taskboard.example.com",
        }
    return fixture


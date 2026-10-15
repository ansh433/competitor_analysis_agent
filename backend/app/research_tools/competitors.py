from pydantic import BaseModel, Field

from app.research_tools.company import (
    CompanyProfile,
    ExtractCompanyProfileInput,
    ExtractProductAndPricingInput,
    FetchWebPageInput,
    FetchedSource,
    ProductAndPricingProfile,
    ResolveCompanyIdentityInput,
    ResolvedCompanyIdentity,
    SearchCompanySourcesInput,
    SourceRecord,
    UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
    extract_company_profile,
    extract_product_and_pricing,
    fetch_web_page,
    resolve_company_identity,
    search_company_sources,
)
from app.research_tools.context import ResearchToolContext


class DiscoverCompetitorsInput(BaseModel):
    company: ResolvedCompanyIdentity
    profile: CompanyProfile
    maximum_candidates: int = Field(default=8, ge=1, le=20)


class CompetitorCandidate(BaseModel):
    name: str
    website: str | None
    relationship_type: str
    proximity: str
    reason: str
    confidence: float = Field(ge=0, le=1)
    evidence_urls: list[str]


class CompetitorDiscovery(BaseModel):
    candidates: list[CompetitorCandidate]
    discovery_notes: list[str]


class ResearchCompetitorInput(BaseModel):
    candidate: CompetitorCandidate


class CompetitorResearch(BaseModel):
    identity: ResolvedCompanyIdentity
    profile: CompanyProfile
    product_and_pricing: ProductAndPricingProfile
    sources: list[SourceRecord]


def discover_competitors(
    tool_input: DiscoverCompetitorsInput,
    context: ResearchToolContext,
) -> CompetitorDiscovery:
    queries = [
        f'"{tool_input.company.canonical_name}" competitors alternatives',
        f'"{tool_input.profile.industry.value or tool_input.company.canonical_name}" leading software vendors',
        f'"{tool_input.company.canonical_name}" versus',
    ]
    search_lines: list[str] = []
    for query in queries:
        response = context.providers.search.search(query, maximum_results=5)
        search_lines.extend(
            f"- {hit.title} | {hit.url} | {hit.snippet}" for hit in response.results
        )
    return context.providers.model.generate_structured(
        UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
        "Identify direct competitors, indirect alternatives, and substitutes. Every candidate needs "
        "an evidence-backed reason and must not be inferred from name similarity alone. Return at "
        f"most {tool_input.maximum_candidates}.\nTARGET: {tool_input.company.model_dump_json()}\n"
        f"PROFILE: {tool_input.profile.model_dump_json()}\n"
        "<UNTRUSTED_SEARCH_RESULTS>\n"
        + "\n".join(search_lines)
        + "\n</UNTRUSTED_SEARCH_RESULTS>",
        CompetitorDiscovery,
    )


def research_competitor(
    tool_input: ResearchCompetitorInput,
    context: ResearchToolContext,
) -> CompetitorResearch:
    identity = resolve_company_identity(
        ResolveCompanyIdentityInput(
            company_name_or_url=tool_input.candidate.website or tool_input.candidate.name
        ),
        context,
    )
    source_output = search_company_sources(
        SearchCompanySourcesInput(
            company=identity,
            focus="all",
            maximum_results=min(8, context.maximum_sources),
        ),
        context,
    )
    fetched: list[FetchedSource] = []
    for source in source_output.sources[:5]:
        fetched.append(fetch_web_page(FetchWebPageInput(url=source.url), context))
    profile = extract_company_profile(
        ExtractCompanyProfileInput(company=identity, sources=fetched), context
    )
    pricing = extract_product_and_pricing(
        ExtractProductAndPricingInput(company=identity, sources=fetched), context
    )
    return CompetitorResearch(
        identity=identity,
        profile=profile,
        product_and_pricing=pricing,
        sources=source_output.sources,
    )


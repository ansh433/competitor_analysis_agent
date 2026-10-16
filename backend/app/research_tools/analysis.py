from datetime import date
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field

from app.research_tools.company import (
    CompanyProfile,
    ProductAndPricingProfile,
    ResolvedCompanyIdentity,
    SourceRecord,
    UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
)
from app.research_tools.competitors import CompetitorResearch
from app.research_tools.context import ResearchToolContext


class SearchCompanyNewsInput(BaseModel):
    company: ResolvedCompanyIdentity
    maximum_results: int = Field(default=10, ge=1, le=30)


class SearchCompanyNewsOutput(BaseModel):
    sources: list[SourceRecord]


class TimelineEvent(BaseModel):
    event_date: date | None
    event_type: Literal[
        "launch", "acquisition", "executive_change", "partnership", "controversy", "other"
    ]
    title: str
    description: str
    classification: Literal["sourced_fact", "analyst_inference", "unavailable_information"]
    evidence_urls: list[str]


class CompanyTimeline(BaseModel):
    events: list[TimelineEvent]
    unavailable_periods: list[str]


class BuildCompanyTimelineInput(BaseModel):
    company: ResolvedCompanyIdentity
    news_sources: list[SourceRecord]


class ComparisonCell(BaseModel):
    company_name: str
    value: str | None
    classification: Literal[
        "sourced_fact", "calculated_result", "analyst_inference", "unavailable_information"
    ]
    evidence_urls: list[str]


class ComparisonRow(BaseModel):
    dimension: str
    cells: list[ComparisonCell]


class ComparisonMatrix(BaseModel):
    company_names: list[str]
    dimensions: list[str]
    rows: list[ComparisonRow]


class BuildComparisonMatrixInput(BaseModel):
    primary_identity: ResolvedCompanyIdentity
    primary_profile: CompanyProfile
    primary_pricing: ProductAndPricingProfile
    competitors: list[CompetitorResearch]
    dimensions: list[str] = Field(
        default_factory=lambda: [
            "Target customer",
            "Core product",
            "Pricing model",
            "Public entry price",
            "Positioning",
        ],
        min_length=1,
        max_length=20,
    )


class RiskSignal(BaseModel):
    title: str
    description: str
    severity: Literal["low", "medium", "high"]
    classification: Literal["verified_fact", "analyst_interpretation", "missing_evidence"]
    evidence_urls: list[str]


class RiskAnalysis(BaseModel):
    contradictions: list[RiskSignal]
    negative_patterns: list[RiskSignal]
    positioning_weaknesses: list[RiskSignal]
    missing_evidence: list[RiskSignal]


class DetectRiskSignalsInput(BaseModel):
    profile: CompanyProfile
    timeline: CompanyTimeline
    comparison: ComparisonMatrix


class ResearchGap(BaseModel):
    question: str
    report_section: str
    reason: str
    priority: Literal["low", "medium", "high"]
    suggested_query: str


class ResearchGapAnalysis(BaseModel):
    gaps: list[ResearchGap]
    coverage_score: float = Field(ge=0, le=1)


class IdentifyResearchGapsInput(BaseModel):
    profile: CompanyProfile
    pricing: ProductAndPricingProfile
    comparison: ComparisonMatrix
    risks: RiskAnalysis
    evidence_count: int = Field(ge=0)


class TargetedResearchInput(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    maximum_results: int = Field(default=4, ge=1, le=10)


class TargetedResearchOutput(BaseModel):
    sources: list[SourceRecord]


def search_company_news(
    tool_input: SearchCompanyNewsInput,
    context: ResearchToolContext,
) -> SearchCompanyNewsOutput:
    response = context.providers.search.search(
        f'"{tool_input.company.canonical_name}" launch acquisition partnership executive controversy',
        maximum_results=min(tool_input.maximum_results, context.maximum_sources),
        topic="news",
    )
    return SearchCompanyNewsOutput(
        sources=[
            SourceRecord(
                title=hit.title,
                url=hit.url,
                snippet=hit.snippet,
                publisher=urlsplit(hit.url).hostname or "unknown",
                source_type="news",
                relevance_score=hit.score,
                published_at=hit.published_at,
            )
            for hit in response.results
        ]
    )


def build_company_timeline(
    tool_input: BuildCompanyTimelineInput,
    context: ResearchToolContext,
) -> CompanyTimeline:
    evidence = "\n".join(
        f"- {source.published_at or 'date unavailable'} | {source.title} | {source.url} | {source.snippet}"
        for source in tool_input.news_sources
    )
    return context.providers.model.generate_structured(
        UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
        f"Build a dated material-event timeline for {tool_input.company.canonical_name}. "
        "Do not assign a date when the source does not provide one.\n"
        f"<UNTRUSTED_NEWS_RESULTS>\n{evidence}\n</UNTRUSTED_NEWS_RESULTS>",
        CompanyTimeline,
    )


def build_comparison_matrix(
    tool_input: BuildComparisonMatrixInput,
    context: ResearchToolContext,
) -> ComparisonMatrix:
    return context.providers.model.generate_structured(
        UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
        "Build a normalized comparison matrix. Keep unavailable values explicit and attach source "
        "URLs to every sourced cell. Do not flatten analyst inference into fact.\n"
        f"DIMENSIONS: {tool_input.dimensions}\n"
        f"PRIMARY: {tool_input.primary_identity.model_dump_json()}\n"
        f"PRIMARY_PROFILE: {tool_input.primary_profile.model_dump_json()}\n"
        f"PRIMARY_PRICING: {tool_input.primary_pricing.model_dump_json()}\n"
        f"COMPETITORS: {[item.model_dump(mode='json') for item in tool_input.competitors]}",
        ComparisonMatrix,
    )


def detect_risk_signals(
    tool_input: DetectRiskSignalsInput,
    context: ResearchToolContext,
) -> RiskAnalysis:
    return context.providers.model.generate_structured(
        UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
        "Detect contradictions, repeated negative events, evidence gaps, and positioning weaknesses. "
        "Separate verified facts from analyst interpretation. A missing source is not a negative fact.\n"
        f"PROFILE: {tool_input.profile.model_dump_json()}\n"
        f"TIMELINE: {tool_input.timeline.model_dump_json()}\n"
        f"COMPARISON: {tool_input.comparison.model_dump_json()}",
        RiskAnalysis,
    )


def identify_research_gaps(
    tool_input: IdentifyResearchGapsInput,
    context: ResearchToolContext,
) -> ResearchGapAnalysis:
    return context.providers.model.generate_structured(
        UNTRUSTED_EVIDENCE_SYSTEM_PROMPT,
        "Identify unanswered report questions and weakly supported sections. Suggested queries must "
        "target the missing evidence instead of repeating broad searches.\n"
        f"EVIDENCE_COUNT: {tool_input.evidence_count}\n"
        f"PROFILE: {tool_input.profile.model_dump_json()}\n"
        f"PRICING: {tool_input.pricing.model_dump_json()}\n"
        f"COMPARISON: {tool_input.comparison.model_dump_json()}\n"
        f"RISKS: {tool_input.risks.model_dump_json()}",
        ResearchGapAnalysis,
    )


def targeted_additional_research(
    tool_input: TargetedResearchInput,
    context: ResearchToolContext,
) -> TargetedResearchOutput:
    response = context.providers.search.search(
        tool_input.query,
        maximum_results=min(tool_input.maximum_results, context.maximum_sources),
    )
    return TargetedResearchOutput(
        sources=[
            SourceRecord(
                title=hit.title,
                url=hit.url,
                snippet=hit.snippet,
                publisher=urlsplit(hit.url).hostname or "unknown",
                source_type="targeted_gap_research",
                relevance_score=hit.score,
                published_at=hit.published_at,
            )
            for hit in response.results
        ]
    )


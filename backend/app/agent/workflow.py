from collections.abc import Callable
from time import perf_counter
from typing import Literal, TypeVar
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from pydantic import BaseModel

from app.agent.state import (
    ClaimVerification,
    EvidenceDraft,
    ResearchGraphContext,
    ResearchState,
    VerificationSummary,
)
from app.research_tools.analysis import (
    BuildCompanyTimelineInput,
    BuildComparisonMatrixInput,
    DetectRiskSignalsInput,
    IdentifyResearchGapsInput,
    SearchCompanyNewsInput,
    TargetedResearchInput,
    build_company_timeline,
    build_comparison_matrix,
    detect_risk_signals,
    identify_research_gaps,
    search_company_news,
    targeted_additional_research,
)
from app.research_tools.company import (
    ExtractCompanyProfileInput,
    ExtractProductAndPricingInput,
    FetchWebPageInput,
    ResolveCompanyIdentityInput,
    SearchCompanySourcesInput,
    extract_company_profile,
    extract_product_and_pricing,
    fetch_web_page,
    resolve_company_identity,
    search_company_sources,
)
from app.research_tools.competitors import (
    DiscoverCompetitorsInput,
    ResearchCompetitorInput,
    discover_competitors,
    research_competitor,
)
from app.research_tools.context import ResearchToolContext
from app.research_tools.reporting import (
    MaterialReportClaim,
    VerifiableEvidence,
    VerifyReportClaimsInput,
    verify_report_claims,
)
from app.streaming.events import GraphStageEnded, GraphStageStarted, ToolEnded, ToolStarted

ToolInput = TypeVar("ToolInput", bound=BaseModel)
ToolOutput = TypeVar("ToolOutput", bound=BaseModel)


def validate_request(state: ResearchState) -> dict[str, object]:
    if len(state["company_input"].strip()) < 2:
        raise ValueError("A company name or website is required")
    if len(state["research_objective"].strip()) < 10:
        raise ValueError("The research objective must describe the intended decision")
    return {}


def resolve_company(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    identity = run_tool(
        "resolve_company_identity",
        ResolveCompanyIdentityInput(company_name_or_url=state["company_input"]),
        resolve_company_identity,
        runtime.context,
    )
    return {"canonical_company": identity}


def create_research_plan(state: ResearchState) -> dict[str, object]:
    company = state["canonical_company"]
    return {
        "research_plan": [
            f"Resolve and profile {company.canonical_name}",
            "Collect official product and pricing sources",
            "Review recent material company events",
            "Discover direct competitors, indirect alternatives, and substitutes",
            "Normalize evidence and compare companies",
            "Close high-priority evidence gaps within the configured loop limit",
            "Synthesize and verify the final dossier",
        ]
    }


def research_official_sources(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    company = state["canonical_company"]
    search = run_tool(
        "search_company_sources",
        SearchCompanySourcesInput(
            company=company,
            focus="all",
            maximum_results=runtime.context.tools.maximum_sources,
        ),
        search_company_sources,
        runtime.context,
    )
    fetched = [
        run_tool(
            "fetch_web_page",
            FetchWebPageInput(url=source.url),
            fetch_web_page,
            runtime.context,
        )
        for source in search.sources[:6]
    ]
    profile = run_tool(
        "extract_company_profile",
        ExtractCompanyProfileInput(company=company, sources=fetched),
        extract_company_profile,
        runtime.context,
    )
    return {"sources": search.sources, "fetched_sources": fetched, "company_profile": profile}


def research_product_and_pricing(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    source_search = run_tool(
        "search_company_sources",
        SearchCompanySourcesInput(
            company=state["canonical_company"],
            focus="pricing",
            maximum_results=min(8, runtime.context.tools.maximum_sources),
        ),
        search_company_sources,
        runtime.context,
    )
    fetched = [
        run_tool(
            "fetch_web_page",
            FetchWebPageInput(url=source.url),
            fetch_web_page,
            runtime.context,
        )
        for source in source_search.sources[:5]
    ]
    pricing = run_tool(
        "extract_product_and_pricing",
        ExtractProductAndPricingInput(
            company=state["canonical_company"],
            sources=fetched,
        ),
        extract_product_and_pricing,
        runtime.context,
    )
    return {"product_and_pricing": pricing}


def research_news_and_events(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    news = run_tool(
        "search_company_news",
        SearchCompanyNewsInput(company=state["canonical_company"]),
        search_company_news,
        runtime.context,
    )
    timeline = run_tool(
        "build_company_timeline",
        BuildCompanyTimelineInput(company=state["canonical_company"], news_sources=news.sources),
        build_company_timeline,
        runtime.context,
    )
    return {"news_sources": news.sources, "company_timeline": timeline}


def discover_competitor_set(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    source_search = run_tool(
        "search_company_sources",
        SearchCompanySourcesInput(
            company=state["canonical_company"], focus="official", maximum_results=4
        ),
        search_company_sources,
        runtime.context,
    )
    fetched = [
        run_tool(
            "fetch_web_page",
            FetchWebPageInput(url=source.url),
            fetch_web_page,
            runtime.context,
        )
        for source in source_search.sources[:3]
    ]
    profile = run_tool(
        "extract_company_profile",
        ExtractCompanyProfileInput(company=state["canonical_company"], sources=fetched),
        extract_company_profile,
        runtime.context,
    )
    discovery = run_tool(
        "discover_competitors",
        DiscoverCompetitorsInput(company=state["canonical_company"], profile=profile),
        discover_competitors,
        runtime.context,
    )
    return {"competitors": discovery.candidates}


def normalize_evidence(state: ResearchState) -> dict[str, object]:
    source_lookup = {source.url: source for source in state.get("fetched_sources", [])}
    drafts: list[EvidenceDraft] = []
    profile = state["company_profile"]
    fields = {
        "legal name": profile.legal_name,
        "industry": profile.industry,
        "headquarters": profile.headquarters,
        "positioning": profile.positioning,
        "business model": profile.business_model,
    }
    for label, field in fields.items():
        if not field.value or not field.source_urls:
            continue
        url = field.source_urls[0]
        source = source_lookup.get(url)
        drafts.append(
            EvidenceDraft(
                claim=f"{state['canonical_company'].canonical_name} {label}: {field.value}",
                source_title=source.title if source else label.title(),
                source_url=url,
                publisher=source.publisher if source else "unknown",
                relevant_excerpt=(source.clean_content[:600] if source else field.value),
                evidence_type="official",
                confidence=0.9,
                fact_classification=field.classification,
            )
        )
    for plan in state["product_and_pricing"].plans:
        drafts.append(
            EvidenceDraft(
                claim=f"{plan.name} public price: {plan.public_price or 'unavailable'}",
                source_title=f"{state['canonical_company'].canonical_name} pricing",
                source_url=plan.source_url,
                publisher=state["canonical_company"].domain,
                relevant_excerpt=f"Plan {plan.name}; public price {plan.public_price or 'not stated'}; billing {plan.billing_basis or 'not stated'}.",
                evidence_type="pricing",
                confidence=0.92 if plan.public_price else 0.7,
                fact_classification=plan.classification,
            )
        )
    return {"evidence_records": drafts}


def research_discovered_competitors(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    researched = [
        run_tool(
            "research_competitor",
            ResearchCompetitorInput(candidate=candidate),
            research_competitor,
            runtime.context,
        )
        for candidate in state.get("competitors", [])[:4]
    ]
    return {"competitor_research": researched}


def build_comparison(
    state: ResearchState, runtime: Runtime[ResearchGraphContext]
) -> dict[str, object]:
    comparison = run_tool(
        "build_comparison_matrix",
        BuildComparisonMatrixInput(
            primary_identity=state["canonical_company"],
            primary_profile=state["company_profile"],
            primary_pricing=state["product_and_pricing"],
            competitors=state.get("competitor_research", []),
        ),
        build_comparison_matrix,
        runtime.context,
    )
    risks = run_tool(
        "detect_risk_signals",
        DetectRiskSignalsInput(
            profile=state["company_profile"],
            timeline=state["company_timeline"],
            comparison=comparison,
        ),
        detect_risk_signals,
        runtime.context,
    )
    return {"comparison_matrix": comparison, "risk_analysis": risks}


def identify_evidence_gaps(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    analysis = run_tool(
        "identify_research_gaps",
        IdentifyResearchGapsInput(
            profile=state["company_profile"],
            pricing=state["product_and_pricing"],
            comparison=state["comparison_matrix"],
            risks=state["risk_analysis"],
            evidence_count=len(state.get("evidence_records", [])),
        ),
        identify_research_gaps,
        runtime.context,
    )
    return {"research_gaps": analysis.gaps, "coverage_score": analysis.coverage_score}


def targeted_gap_research(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    gaps = state.get("research_gaps", [])
    if not gaps:
        return {"loop_count": state["loop_count"] + 1}
    result = run_tool(
        "targeted_additional_research",
        TargetedResearchInput(
            query=gaps[0].suggested_query,
            maximum_results=min(4, runtime.context.tools.maximum_sources),
        ),
        targeted_additional_research,
        runtime.context,
    )
    fetched = [
        run_tool(
            "fetch_web_page",
            FetchWebPageInput(url=source.url),
            fetch_web_page,
            runtime.context,
        )
        for source in result.sources[:3]
    ]
    additional_evidence = [
        EvidenceDraft(
            claim=f"Targeted evidence for: {gaps[0].question}",
            source_title=source.title,
            source_url=source.url,
            publisher=source.publisher,
            relevant_excerpt=source.clean_content[:600],
            evidence_type="other",
            confidence=0.72,
            fact_classification="sourced_fact",
        )
        for source in fetched
    ]
    return {
        "sources": [*state.get("sources", []), *result.sources],
        "fetched_sources": [*state.get("fetched_sources", []), *fetched],
        "evidence_records": [*state.get("evidence_records", []), *additional_evidence],
        "loop_count": state["loop_count"] + 1,
    }


def route_after_gap_analysis(
    state: ResearchState,
) -> Literal["targeted_gap_research", "synthesize_dossier"]:
    if state.get("research_gaps") and state["loop_count"] < state["maximum_gap_loops"]:
        return "targeted_gap_research"
    return "synthesize_dossier"


def synthesize_dossier(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    del runtime
    evidence = list(state.get("evidence_records", []))
    company = state["canonical_company"]
    first_source = (state.get("fetched_sources", []) or [None])[0]
    if first_source:
        evidence.append(
            EvidenceDraft(
                claim=f"{company.canonical_name} products: {', '.join(state['company_profile'].products)}",
                source_title=first_source.title,
                source_url=first_source.url,
                publisher=first_source.publisher,
                relevant_excerpt=first_source.clean_content[:600],
                evidence_type="product_documentation",
                confidence=0.86,
                fact_classification="sourced_fact",
            )
        )
    for candidate in state.get("competitors", []):
        if candidate.evidence_urls:
            evidence.append(
                EvidenceDraft(
                    claim=f"{candidate.name} is a {candidate.proximity} {candidate.relationship_type}: {candidate.reason}",
                    source_title=f"Competitive relationship: {candidate.name}",
                    source_url=candidate.evidence_urls[0],
                    publisher="external source",
                    relevant_excerpt=candidate.reason,
                    evidence_type="other",
                    confidence=candidate.confidence,
                    fact_classification="analyst_inference",
                )
            )
    for event in state["company_timeline"].events:
        if event.evidence_urls:
            evidence.append(
                EvidenceDraft(
                    claim=f"{event.title}: {event.description}",
                    source_title=event.title,
                    source_url=event.evidence_urls[0],
                    publisher="news source",
                    relevant_excerpt=event.description,
                    evidence_type="news",
                    confidence=0.84,
                    fact_classification=event.classification,
                )
            )
    for row in state["comparison_matrix"].rows:
        for cell in row.cells:
            if cell.value and cell.evidence_urls:
                evidence.append(
                    EvidenceDraft(
                        claim=f"{cell.company_name} {row.dimension}: {cell.value}",
                        source_title=f"{cell.company_name} {row.dimension}",
                        source_url=cell.evidence_urls[0],
                        publisher="comparison source",
                        relevant_excerpt=cell.value,
                        evidence_type="other",
                        confidence=0.82,
                        fact_classification=cell.classification,
                    )
                )

    claims: list[MaterialReportClaim] = []

    def record_claim(
        claim: str,
        section: str,
        classification: str,
        matching_text: str,
    ) -> str:
        match = next(
            (item for item in evidence if matching_text.lower() in item.claim.lower()), None
        )
        evidence_ids = [match.id] if match else []
        normalized_classification = (
            classification
            if classification
            in {
                "sourced_fact",
                "calculated_result",
                "analyst_inference",
                "unavailable_information",
            }
            else "analyst_inference"
        )
        claims.append(
            MaterialReportClaim(
                claim=claim,
                report_section=section,
                classification=normalized_classification,
                evidence_ids=evidence_ids,
            )
        )
        label = normalized_classification.replace("_", " ").title()
        citation = f" [Evidence {match.id.hex[:8]}](/api/v1/evidence/{match.id})" if match else ""
        return f"- **{label}:** {claim}{citation}"

    profile = state["company_profile"]
    pricing = state["product_and_pricing"]
    competitor_lines = [
        record_claim(
            f"{candidate.name}: {candidate.reason}",
            "Direct competitors"
            if candidate.proximity == "direct"
            else "Indirect competitors and substitutes",
            "analyst_inference",
            candidate.name,
        )
        for candidate in state.get("competitors", [])
    ]
    profile_lines = []
    for label, field in (
        ("Legal name", profile.legal_name),
        ("Industry", profile.industry),
        ("Headquarters", profile.headquarters),
        ("Business model", profile.business_model),
    ):
        value = field.value or "Unavailable in reviewed sources"
        profile_lines.append(
            record_claim(
                f"{label}: {value}",
                "Canonical company profile",
                field.classification,
                label.lower(),
            )
        )
    product_claim = record_claim(
        ", ".join(profile.products) or "Product details unavailable",
        "Product and service overview",
        "sourced_fact" if profile.products else "unavailable_information",
        "products",
    )
    pricing_lines = [
        record_claim(
            f"{plan.name}: {plan.public_price or 'public price unavailable'} ({plan.billing_basis or 'billing basis unavailable'})",
            "Pricing/business-model comparison",
            plan.classification,
            plan.name,
        )
        for plan in pricing.plans
    ]
    timeline_lines = [
        record_claim(
            f"{event.event_date or 'Date unavailable'} — {event.title}: {event.description}",
            "Material news/event timeline",
            event.classification,
            event.title,
        )
        for event in state["company_timeline"].events
    ]

    matrix_lines = [
        "| Dimension | " + " | ".join(state["comparison_matrix"].company_names) + " |",
        "|---|" + "---|" * len(state["comparison_matrix"].company_names),
    ]
    for row in state["comparison_matrix"].rows:
        values: list[str] = []
        for cell in row.cells:
            if not cell.value:
                values.append("Unavailable information")
                continue
            matching = next(
                (
                    item
                    for item in evidence
                    if cell.company_name.lower() in item.claim.lower()
                    and row.dimension.lower() in item.claim.lower()
                ),
                None,
            )
            evidence_ids = [matching.id] if matching else []
            claims.append(
                MaterialReportClaim(
                    claim=f"{cell.company_name} {row.dimension}: {cell.value}",
                    report_section="Feature comparison matrix",
                    classification=cell.classification,
                    evidence_ids=evidence_ids,
                )
            )
            citation = (
                f" [Evidence {matching.id.hex[:8]}](/api/v1/evidence/{matching.id})"
                if matching
                else ""
            )
            values.append(f"{cell.value}{citation}")
        matrix_lines.append(f"| {row.dimension} | " + " | ".join(values) + " |")

    risk_lines = [
        f"- **{signal.classification.replace('_', ' ').title()}:** {signal.title} — {signal.description}"
        for signals in (
            state["risk_analysis"].contradictions,
            state["risk_analysis"].negative_patterns,
            state["risk_analysis"].positioning_weaknesses,
            state["risk_analysis"].missing_evidence,
        )
        for signal in signals
    ]
    gap_lines = [
        f"- **{gap.priority.title()}:** {gap.question} — {gap.reason}"
        for gap in state.get("research_gaps", [])
    ]
    evidence_lines = [
        f'- <a id="evidence-{item.id}"></a> **{item.fact_classification.replace("_", " ").title()}** — {item.claim}. [Evidence record](/api/v1/evidence/{item.id}) · [Source]({item.source_url})'
        for item in evidence
    ]
    direct = [
        line
        for candidate, line in zip(state.get("competitors", []), competitor_lines, strict=True)
        if candidate.proximity == "direct"
    ]
    indirect = [
        line
        for candidate, line in zip(state.get("competitors", []), competitor_lines, strict=True)
        if candidate.proximity != "direct"
    ]
    report = "\n\n".join(
        [
            f"# {company.canonical_name} competitor intelligence dossier",
            f"## 1. Executive summary\n\n**Analyst inference:** This dossier evaluates {company.canonical_name} for the stated objective using {len(evidence)} evidence records. Material facts below link to the evidence ledger.",
            "## 2. Canonical company profile\n\n" + "\n".join(profile_lines),
            "## 3. Product and service overview\n\n" + product_claim,
            "## 4. Target customer and positioning analysis\n\n"
            + record_claim(
                profile.positioning.value or "Positioning unavailable",
                "Target customer and positioning analysis",
                profile.positioning.classification,
                "positioning",
            ),
            "## 5. Direct competitors\n\n"
            + (
                "\n".join(direct)
                or "- **Unavailable information:** No direct competitor was sufficiently supported."
            ),
            "## 6. Indirect competitors and substitutes\n\n"
            + (
                "\n".join(indirect)
                or "- **Unavailable information:** No indirect alternative was sufficiently supported."
            ),
            "## 7. Feature comparison matrix\n\n" + "\n".join(matrix_lines),
            "## 8. Pricing/business-model comparison\n\n"
            + (
                "\n".join(pricing_lines)
                or "- **Unavailable information:** No public prices were located."
            ),
            "## 9. Strengths and weaknesses\n\n"
            + ("\n".join(risk_lines) or "- No supported risk pattern was identified."),
            "## 10. Market-positioning observations\n\n**Analyst inference:** Positioning observations are derived from the sourced profile and normalized comparison, not represented as company-stated facts.",
            "## 11. Material news/event timeline\n\n"
            + (
                "\n".join(timeline_lines)
                or "- **Unavailable information:** No material dated events were located."
            ),
            "## 12. Risks and contradictions\n\n"
            + (
                "\n".join(risk_lines)
                or "- No verified contradiction was identified in the reviewed evidence."
            ),
            "## 13. Research gaps\n\n"
            + ("\n".join(gap_lines) or "- No high-priority gap remains."),
            "## 14. Recommended follow-up questions\n\n"
            + (
                "\n".join(f"- {gap.question}" for gap in state.get("research_gaps", []))
                or "- Revalidate material claims when new primary sources appear."
            ),
            "## 15. Evidence ledger\n\n" + "\n".join(evidence_lines),
            f"## 16. Coverage and confidence\n\n- **Calculated result:** Coverage score {state.get('coverage_score', 0.0):.0%}.\n- **Calculated result:** Confidence score {(sum(item.confidence for item in evidence) / len(evidence) if evidence else 0.0):.0%}.",
        ]
    )
    confidence = sum(item.confidence for item in evidence) / len(evidence) if evidence else 0.0
    return {
        "evidence_records": evidence,
        "draft_report": report,
        "draft_claims": claims,
        "confidence_score": confidence,
    }


def verify_claims_and_citations_with_context(
    state: ResearchState,
    runtime: Runtime[ResearchGraphContext],
) -> dict[str, object]:
    result = run_tool(
        "verify_report_claims",
        VerifyReportClaimsInput(
            report_markdown=state["draft_report"],
            claims=state.get("draft_claims", []),
            evidence=[
                VerifiableEvidence(
                    evidence_id=item.id,
                    claim=item.claim,
                    source_url=item.source_url,
                    classification=item.fact_classification,
                )
                for item in state.get("evidence_records", [])
            ],
        ),
        verify_report_claims,
        runtime.context,
    )
    return {
        "verification_results": VerificationSummary(
            passed=result.passed,
            claims=[
                ClaimVerification(
                    claim=item.claim,
                    supported=item.supported,
                    evidence_urls=[
                        f"/api/v1/evidence/{evidence_id}" for evidence_id in item.evidence_ids
                    ],
                    reason=item.reason,
                )
                for item in result.claims
            ],
            unsupported_claims=result.unsupported_claims,
        )
    }


def revise_dossier(state: ResearchState) -> dict[str, object]:
    unsupported = set(state["verification_results"].unsupported_claims)
    report = state["draft_report"]
    revised_claims: list[MaterialReportClaim] = []
    for claim in state.get("draft_claims", []):
        if claim.claim in unsupported:
            report = report.replace(
                claim.claim, "Unavailable information after citation verification"
            )
            revised_claims.append(
                MaterialReportClaim(
                    claim="Unavailable information after citation verification",
                    report_section=claim.report_section,
                    classification="unavailable_information",
                    evidence_ids=[],
                )
            )
        else:
            revised_claims.append(claim)
    return {"draft_report": report, "draft_claims": revised_claims}


def route_after_verification(
    state: ResearchState,
) -> Literal["revise_dossier", "persist_artifacts"]:
    return "persist_artifacts" if state["verification_results"].passed else "revise_dossier"


def persist_artifacts(state: ResearchState) -> dict[str, object]:
    return {
        "final_artifact": {
            "research_run_id": str(state["research_run_id"]),
            "report_markdown": state["draft_report"],
            "coverage_score": state.get("coverage_score", 0.0),
            "confidence_score": state.get("confidence_score", 0.0),
            "verification_passed": state["verification_results"].passed,
        }
    }


def build_competitor_research_graph():
    builder = StateGraph(ResearchState, context_schema=ResearchGraphContext)
    builder.add_node("validate_request", stage_node("validate_request", 0, validate_request, False))
    builder.add_node("resolve_company", stage_node("resolve_company", 1, resolve_company, True))
    builder.add_node(
        "create_research_plan", stage_node("create_research_plan", 2, create_research_plan, False)
    )
    builder.add_node(
        "research_official_sources",
        stage_node("research_official_sources", 3, research_official_sources, True),
    )
    builder.add_node(
        "research_product_and_pricing",
        stage_node("research_product_and_pricing", 4, research_product_and_pricing, True),
    )
    builder.add_node(
        "research_news_and_events",
        stage_node("research_news_and_events", 5, research_news_and_events, True),
    )
    builder.add_node(
        "discover_competitors", stage_node("discover_competitors", 6, discover_competitor_set, True)
    )
    builder.add_node(
        "normalize_evidence", stage_node("normalize_evidence", 7, normalize_evidence, False)
    )
    builder.add_node(
        "research_discovered_competitors",
        stage_node("research_discovered_competitors", 8, research_discovered_competitors, True),
    )
    builder.add_node("build_comparison", stage_node("build_comparison", 9, build_comparison, True))
    builder.add_node(
        "identify_evidence_gaps",
        stage_node("identify_evidence_gaps", 10, identify_evidence_gaps, True),
    )
    builder.add_node(
        "targeted_gap_research",
        stage_node("targeted_gap_research", 11, targeted_gap_research, True),
    )
    builder.add_node(
        "synthesize_dossier", stage_node("synthesize_dossier", 12, synthesize_dossier, True)
    )
    builder.add_node(
        "verify_claims_and_citations",
        stage_node(
            "verify_claims_and_citations", 13, verify_claims_and_citations_with_context, True
        ),
    )
    builder.add_node("revise_dossier", stage_node("revise_dossier", 14, revise_dossier, False))
    builder.add_node(
        "persist_artifacts", stage_node("persist_artifacts", 15, persist_artifacts, False)
    )
    builder.add_conditional_edges(
        START,
        route_graph_entry,
        [
            "validate_request",
            "resolve_company",
            "create_research_plan",
            "normalize_evidence",
            "research_discovered_competitors",
            "build_comparison",
            "identify_evidence_gaps",
            "targeted_gap_research",
            "synthesize_dossier",
            "verify_claims_and_citations",
            "revise_dossier",
            "persist_artifacts",
        ],
    )
    builder.add_edge("validate_request", "resolve_company")
    builder.add_edge("resolve_company", "create_research_plan")
    builder.add_edge("create_research_plan", "research_official_sources")
    builder.add_edge("create_research_plan", "research_product_and_pricing")
    builder.add_edge("create_research_plan", "research_news_and_events")
    builder.add_edge("create_research_plan", "discover_competitors")
    builder.add_edge(
        [
            "research_official_sources",
            "research_product_and_pricing",
            "research_news_and_events",
            "discover_competitors",
        ],
        "normalize_evidence",
    )
    builder.add_edge("normalize_evidence", "research_discovered_competitors")
    builder.add_edge("research_discovered_competitors", "build_comparison")
    builder.add_edge("build_comparison", "identify_evidence_gaps")
    builder.add_conditional_edges(
        "identify_evidence_gaps",
        route_after_gap_analysis,
        ["targeted_gap_research", "synthesize_dossier"],
    )
    builder.add_edge("targeted_gap_research", "identify_evidence_gaps")
    builder.add_edge("synthesize_dossier", "verify_claims_and_citations")
    builder.add_conditional_edges(
        "verify_claims_and_citations",
        route_after_verification,
        ["revise_dossier", "persist_artifacts"],
    )
    builder.add_edge("revise_dossier", "verify_claims_and_citations")
    builder.add_edge("persist_artifacts", END)
    return builder.compile()


def stage_node(
    name: str,
    index: int,
    node: Callable[..., dict[str, object]],
    uses_runtime: bool,
) -> Callable[[ResearchState, Runtime[ResearchGraphContext]], dict[str, object]]:
    def wrapped(
        state: ResearchState,
        runtime: Runtime[ResearchGraphContext],
    ) -> dict[str, object]:
        runtime.context.emit(
            GraphStageStarted(stage_name=name, stage_index=index, detail=f"Starting {name}")
        )
        try:
            result = node(state, runtime) if uses_runtime else node(state)
        except Exception:
            runtime.context.checkpoint(name, {}, "failed")
            runtime.context.emit(
                GraphStageEnded(stage_name=name, stage_index=index, detail=f"Failed {name}")
            )
            raise
        runtime.context.checkpoint(name, result, "completed")
        runtime.context.emit(
            GraphStageEnded(stage_name=name, stage_index=index, detail=f"Completed {name}")
        )
        return result

    return wrapped


def route_graph_entry(state: ResearchState) -> str:
    return state.get("resume_from_stage", "validate_request")


COMPETITOR_RESEARCH_GRAPH = build_competitor_research_graph()


def run_tool(
    name: str,
    tool_input: ToolInput,
    tool: Callable[[ToolInput, ResearchToolContext], ToolOutput],
    graph_context: ResearchGraphContext,
) -> ToolOutput:
    execution_id = uuid4()
    graph_context.emit(
        ToolStarted(
            execution_id=execution_id,
            tool_name=name,
            arguments=tool_input.model_dump(mode="json"),
        )
    )
    started = perf_counter()
    try:
        output = tool(tool_input, graph_context.tools)
    except Exception as error:
        graph_context.emit(
            ToolEnded(
                execution_id=execution_id,
                tool_name=name,
                output={"error": type(error).__name__},
                execution_time_ms=int((perf_counter() - started) * 1000),
                success=False,
            )
        )
        raise
    graph_context.emit(
        ToolEnded(
            execution_id=execution_id,
            tool_name=name,
            output=output.model_dump(mode="json"),
            execution_time_ms=int((perf_counter() - started) * 1000),
            success=True,
        )
    )
    return output

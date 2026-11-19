# LangGraph topology

The application compiles an explicit `StateGraph`; it does not use a prebuilt ReAct loop.

```mermaid
flowchart TD
    START --> Validate[validate_request]
    Validate --> Resolve[resolve_company]
    Resolve --> Plan[create_research_plan]
    Plan --> Official[official sources]
    Plan --> Pricing[product and pricing]
    Plan --> News[news and events]
    Plan --> Discover[competitor discovery]
    Official --> Normalize[normalize_evidence]
    Pricing --> Normalize
    News --> Normalize
    Discover --> Normalize
    Normalize --> Competitors[research_discovered_competitors]
    Competitors --> Compare[build_comparison]
    Compare --> Gaps[identify_evidence_gaps]
    Gaps -->|gaps and loop below limit| Targeted[targeted_gap_research]
    Targeted --> Gaps
    Gaps -->|sufficient or limit reached| Synthesize[synthesize_dossier]
    Synthesize --> Verify[verify_claims_and_citations]
    Verify -->|failed| Revise[revise_dossier]
    Revise --> Verify
    Verify -->|passed| Persist[persist_artifacts]
    Persist --> END
```

Every stage wrapper persists its merged state update. A retryable provider failure saves the failed stage and returns a paused stream event. `POST /research-runs/{id}/resume` re-enters the graph at that stage; failures in the initial parallel fan-out restart only the parallel research phase so the join remains valid.

State contains authenticated IDs, objective, canonical identity, plan, sources, evidence drafts, profiles, competitor candidates, normalized comparison, risks, gaps, loop count, packed conversation context, report claims, verification output, and final artifact metadata.

Parallel branches update distinct state keys and join at `normalize_evidence`. The gap loop is bounded by `MAXIMUM_GAP_RESEARCH_LOOPS`. Each node emits stage start/end events. Tool execution emits its own start/end pair and measures only that tool's duration.

The system prompt is passed on every model call. Retrieved content is wrapped in explicit untrusted-source delimiters and is never treated as instructions.


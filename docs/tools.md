# Tool contracts

All tool inputs and outputs are Pydantic models. Every tool receives an explicit authenticated `ResearchToolContext`.

| Tool | Input | Output and guarantees |
|---|---|---|
| `resolve_company_identity` | Name or URL | Canonical identity, confidence, and explicit ambiguities |
| `search_company_sources` | Canonical identity, focus, limit | Deduplicated official, product, pricing, and announcement sources |
| `fetch_web_page` | Validated public URL | Clean content, title, publisher, final URL, and retrieval time |
| `extract_company_profile` | Identity and fetched sources | Normalized profile fields with availability and source URLs |
| `extract_product_and_pricing` | Identity and sources | Products, public plans, pricing basis, differentiators, unavailable fields |
| `discover_competitors` | Identity and profile | Direct, indirect, and substitute candidates with reasons and evidence |
| `research_competitor` | Candidate | Same normalized identity/profile/pricing shape used for the primary company |
| `search_company_news` | Identity and limit | Recent company-event sources |
| `build_company_timeline` | Identity and news sources | Dated launches, acquisitions, changes, partnerships, and controversies |
| `build_comparison_matrix` | Primary and competitor research | Dimension-normalized cells with fact/inference/unavailable labels |
| `detect_risk_signals` | Profile, timeline, comparison | Contradictions, patterns, weaknesses, and missing evidence |
| `identify_research_gaps` | Research artifacts | Prioritized unanswered questions and targeted queries |
| `targeted_additional_research` | Gap query and limit | Additional sources for the bounded loop |
| `verify_report_claims` | Report, material claims, evidence | Per-claim citation decision and overall pass/fail |
| `persist_research_artifact` | Verified dossier package | Persisted run, evidence, competitor relationships, and comparison IDs |

Live adapters can raise a safe `ExternalProviderError`; the stream records a typed error and marks the run failed without exposing provider credentials or raw authorization data.


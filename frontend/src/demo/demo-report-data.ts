import type { EvidenceArtifact } from "../research/artifact-types";

const evidenceIds = {
  product: "d81b2be1-8a31-4bb4-a8b2-1fc19e0810c1",
  pricing: "a6e9c310-697a-4fe9-a41c-f6791a0b2ed3",
  hiring: "73b8f10d-e95a-4349-8a87-6cd8e4c52738",
  inference: "cc0d1941-31df-4ca9-8fc4-f3a7e31ee9e5",
  calculation: "3f6d12a4-2d8f-4e1a-a64e-37a9d9e8fca2",
  gap: "f2a2b62d-33e4-4f1f-9e44-8e4dd60ff19b",
} as const;

/** A deliberately varied dossier for inspecting the shared report renderer. */
export const demoReportMarkdown = `# Competitive intelligence dossier

## 1. Executive summary

Northstar Workspace is a fictional collaboration product used here to exercise the full report surface. **sourced_fact** The product describes a shared workspace for decision records and project context [source](/api/v1/evidence/${evidenceIds.product}).

**analyst_inference** Its language suggests a buyer who values durable context more than lightweight task capture [analysis](/api/v1/evidence/${evidenceIds.inference}).

## 2. Identity and operating context

| Field | Finding | Status |
| --- | --- | --- |
| Legal name | Northstar Workspace, Inc. | **sourced_fact** |
| Headquarters | Portland, Oregon | **sourced_fact** |
| Enterprise price | Not published | **unavailable_information** |

## 3. Product thesis

The illustrative product combines decision logs, project references, and review queues. It is presented as a system of record rather than another chat channel.

## 4. Customer signals

- Teams with recurring cross-functional reviews
- Product and operations leaders
- Organisations replacing scattered meeting notes

## 5. Commercial model

**sourced_fact** The public plan page lists an individual and team tier [pricing page](/api/v1/evidence/${evidenceIds.pricing}).

**unavailable_information** Contract terms, volume discounts, and enterprise minimums could not be resolved from public material.

## 6. Market posture

Northstar is framed as a decision workspace. **calculated_result** Of the five comparison dimensions below, three are supported by direct source material [coverage calculation](/api/v1/evidence/${evidenceIds.calculation}).

## 7. Feature comparison matrix

| Dimension | Northstar | Linear | Notion | Asana | Coda |
| --- | --- | --- | --- | --- | --- |
| Decision log | Native review records | Project updates | Database template | Status update | Document table |
| Structured research | Evidence fields | Issue context | Wiki pages | Project briefs | Pack documents |
| Project planning | Lightweight | Deep issue planning | Flexible blocks | Work management | Flexible tables |
| Enterprise pricing | **unavailable_information** | Public tier | Public tier | Public tier | Contact sales |
| Positioning | **analyst_inference** Context system | Product development | Connected workspace | Work coordination | Doc-first apps |

## 8. Competitive strengths

1. A dedicated place for decisions and supporting evidence.
2. A report format that distinguishes a source from an interpretation.
3. A narrower workflow than general-purpose work hubs.

## 9. Competitive constraints

The fictional product has less established project planning depth than specialist tools. This is an illustrative assessment, not a market claim.

## 10. Pricing and packaging

**sourced_fact** The team tier is described as a per-seat subscription [plan evidence](/api/v1/evidence/${evidenceIds.pricing}). The public material does not describe procurement terms.

## 11. Go-to-market signals

**sourced_fact** A sample careers listing describes roles across product and go-to-market functions [careers evidence](/api/v1/evidence/${evidenceIds.hiring}).

## 12. Risk factors

- Evidence freshness varies by source.
- Pricing gaps should not be treated as a free offering.
- Competitor claims need their own source records.

## 13. Open questions

**unavailable_information** Does Northstar offer a self-hosted deployment option?

**unavailable_information** Which compliance certifications are contractually available?

## 14. Recommended next checks

1. Request a current enterprise quote.
2. Confirm integration coverage in a live product walkthrough.
3. Validate usage with a customer reference.

## 15. Evidence ledger

The ledger below is generated from the report evidence records.

## 16. Research quality

Coverage is intentionally incomplete so that sourced claims, calculations, inferences, and gaps all appear in the same dossier.`;

export const demoEvidence: EvidenceArtifact[] = [
  {
    id: evidenceIds.product,
    claim:
      "Northstar describes a shared workspace for decision records and project context.",
    source_title: "Northstar product overview",
    source_url: "https://example.com/northstar/product",
    publisher: "Northstar Workspace",
    relevant_excerpt:
      "Bring the decisions, supporting context, and next actions from a project into one shared review record.",
    evidence_type: "product_page",
    confidence: 0.94,
    fact_classification: "sourced_fact",
    verification_status: "verified",
  },
  {
    id: evidenceIds.pricing,
    claim:
      "The public plan page presents individual and team subscription tiers.",
    source_title: "Northstar plans",
    source_url: "https://example.com/northstar/pricing",
    publisher: "Northstar Workspace",
    relevant_excerpt:
      "Choose an individual workspace or a shared team workspace billed per member.",
    evidence_type: "pricing_page",
    confidence: 0.9,
    fact_classification: "sourced_fact",
    verification_status: "verified",
  },
  {
    id: evidenceIds.hiring,
    claim:
      "A careers listing illustrates roles across product and go-to-market functions.",
    source_title: "Northstar careers",
    source_url: "https://example.com/northstar/careers",
    publisher: "Northstar Workspace",
    relevant_excerpt:
      "Open roles span product design, platform engineering, customer success, and partnerships.",
    evidence_type: "careers_page",
    confidence: 0.78,
    fact_classification: "sourced_fact",
    verification_status: "verified",
  },
  {
    id: evidenceIds.inference,
    claim:
      "The product language suggests an emphasis on durable organisational context.",
    source_title: "Analyst synthesis",
    source_url: "https://example.com/northstar/analysis",
    relevant_excerpt:
      "This interpretation connects repeated language about records, review, and traceability; it is not a company statement.",
    evidence_type: "analyst_synthesis",
    confidence: 0.66,
    fact_classification: "analyst_inference",
    verification_status: "derived",
  },
  {
    id: evidenceIds.calculation,
    claim:
      "Three of five comparison dimensions have direct supporting material.",
    source_title: "Evidence coverage calculation",
    source_url: "https://example.com/northstar/coverage-method",
    publisher: "Compass calculation",
    relevant_excerpt:
      "The ratio is calculated from three directly supported dimensions divided by five reviewed comparison dimensions.",
    evidence_type: "calculation",
    confidence: 1,
    fact_classification: "calculated_result",
    verification_status: "calculated",
  },
  {
    id: evidenceIds.gap,
    claim:
      "Enterprise price and procurement requirements remain unavailable in the reviewed material.",
    source_title: "Research gap",
    source_url: "https://example.com/northstar/research-gap",
    relevant_excerpt:
      "The sample review found no published enterprise pricing, contractual minimum, or procurement terms.",
    evidence_type: "research_gap",
    confidence: 0.35,
    fact_classification: "unavailable_information",
    verification_status: "unavailable",
  },
];

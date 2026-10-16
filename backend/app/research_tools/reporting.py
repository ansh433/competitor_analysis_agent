from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.research_tools.context import ResearchToolContext


class MaterialReportClaim(BaseModel):
    claim: str
    report_section: str
    classification: Literal[
        "sourced_fact", "calculated_result", "analyst_inference", "unavailable_information"
    ]
    evidence_ids: list[UUID]


class VerifiableEvidence(BaseModel):
    evidence_id: UUID
    claim: str
    source_url: str
    classification: str
    accepted: bool = True


class VerifyReportClaimsInput(BaseModel):
    report_markdown: str
    claims: list[MaterialReportClaim]
    evidence: list[VerifiableEvidence]


class VerifiedReportClaim(BaseModel):
    claim: str
    supported: bool
    evidence_ids: list[UUID]
    reason: str


class ReportVerificationResult(BaseModel):
    passed: bool
    claims: list[VerifiedReportClaim]
    unsupported_claims: list[str]


def verify_report_claims(
    tool_input: VerifyReportClaimsInput,
    _context: ResearchToolContext,
) -> ReportVerificationResult:
    accepted_evidence = {
        item.evidence_id: item for item in tool_input.evidence if item.accepted and item.source_url
    }
    verified: list[VerifiedReportClaim] = []
    for claim in tool_input.claims:
        if claim.classification == "unavailable_information":
            supported = True
            reason = "Explicitly labelled unavailable information"
        else:
            supported_ids = [item for item in claim.evidence_ids if item in accepted_evidence]
            links_present = all(
                f"/api/v1/evidence/{evidence_id}" in tool_input.report_markdown
                for evidence_id in supported_ids
            )
            supported = bool(supported_ids) and links_present
            reason = (
                "Claim links accepted evidence records"
                if supported
                else "Material claim lacks an accepted linked evidence record"
            )
        verified.append(
            VerifiedReportClaim(
                claim=claim.claim,
                supported=supported,
                evidence_ids=claim.evidence_ids,
                reason=reason,
            )
        )
    unsupported = [claim.claim for claim in verified if not claim.supported]
    return ReportVerificationResult(
        passed=bool(verified) and not unsupported,
        claims=verified,
        unsupported_claims=unsupported,
    )


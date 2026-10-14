from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConversationIdentified(BaseModel):
    kind: Literal["conversation_identified"] = "conversation_identified"
    conversation_id: UUID


class ResearchRunIdentified(BaseModel):
    kind: Literal["research_run_identified"] = "research_run_identified"
    research_run_id: UUID


class TextChunk(BaseModel):
    kind: Literal["text_chunk"] = "text_chunk"
    text: str
    is_final_chunk: bool = False


class GraphStageStarted(BaseModel):
    kind: Literal["graph_stage_started"] = "graph_stage_started"
    stage_name: str
    stage_index: int = Field(ge=0)
    detail: str = ""


class GraphStageEnded(BaseModel):
    kind: Literal["graph_stage_ended"] = "graph_stage_ended"
    stage_name: str
    stage_index: int = Field(ge=0)
    detail: str = ""


class ToolStarted(BaseModel):
    kind: Literal["tool_started"] = "tool_started"
    execution_id: UUID
    tool_name: str
    arguments: dict[str, object]


class ToolEnded(BaseModel):
    kind: Literal["tool_ended"] = "tool_ended"
    execution_id: UUID
    tool_name: str
    output: dict[str, object]
    execution_time_ms: int = Field(ge=0)
    success: bool


class SourceDiscovered(BaseModel):
    kind: Literal["source_discovered"] = "source_discovered"
    source_id: UUID
    title: str
    url: str
    publisher: str


class EvidenceAccepted(BaseModel):
    kind: Literal["evidence_accepted"] = "evidence_accepted"
    evidence_id: UUID
    claim: str
    source_url: str
    reason: str = ""
    confidence: float = Field(ge=0, le=1)


class EvidenceRejected(BaseModel):
    kind: Literal["evidence_rejected"] = "evidence_rejected"
    evidence_id: UUID
    claim: str
    source_url: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class ResearchGapFound(BaseModel):
    kind: Literal["research_gap_found"] = "research_gap_found"
    gap_id: UUID
    question: str
    report_section: str


class ComparisonArtifact(BaseModel):
    kind: Literal["comparison_artifact"] = "comparison_artifact"
    comparison_id: UUID
    structured_result: dict[str, object]


class FinalReportArtifact(BaseModel):
    kind: Literal["final_report_artifact"] = "final_report_artifact"
    research_run_id: UUID
    report_markdown: str
    confidence_score: float = Field(ge=0, le=1)
    coverage_score: float = Field(ge=0, le=1)


class StreamError(BaseModel):
    kind: Literal["error"] = "error"
    code: str
    message: str
    retryable: bool = False


class StreamFinished(BaseModel):
    kind: Literal["finished"] = "finished"
    success: bool


StreamPayload = Annotated[
    ConversationIdentified
    | ResearchRunIdentified
    | TextChunk
    | GraphStageStarted
    | GraphStageEnded
    | ToolStarted
    | ToolEnded
    | SourceDiscovered
    | EvidenceAccepted
    | EvidenceRejected
    | ResearchGapFound
    | ComparisonArtifact
    | FinalReportArtifact
    | StreamError
    | StreamFinished,
    Field(discriminator="kind"),
]


class StreamEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: StreamPayload


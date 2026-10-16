import type { INamespace } from "protobufjs";
import protobuf from "protobufjs/light";

import generatedSchema from "./competitor-events.schema.json";

const schema = generatedSchema as INamespace;

interface WireEvent {
  eventId: string;
  timestamp: string;
  conversationIdentified?: { conversationId: string };
  researchRunIdentified?: { researchRunId: string };
  textChunk?: { text: string; isFinalChunk: boolean };
  graphStageStarted?: { stageName: string; stageIndex: number; detail: string };
  graphStageEnded?: { stageName: string; stageIndex: number; detail: string };
  toolStarted?: {
    executionId: string;
    toolName: string;
    argumentsJson: string;
  };
  toolEnded?: {
    executionId: string;
    toolName: string;
    outputJson: string;
    executionTimeMs: number;
    success: boolean;
  };
  sourceDiscovered?: {
    sourceId: string;
    title: string;
    url: string;
    publisher: string;
  };
  evidenceAccepted?: EvidenceWirePayload;
  evidenceRejected?: EvidenceWirePayload;
  researchGapFound?: { gapId: string; question: string; reportSection: string };
  comparisonArtifact?: { comparisonId: string; structuredResultJson: string };
  finalReportArtifact?: {
    researchRunId: string;
    reportMarkdown: string;
    confidenceScore: number;
    coverageScore: number;
  };
  error?: { code: string; message: string; retryable: boolean };
  finished?: { success: boolean };
}

interface EvidenceWirePayload {
  evidenceId: string;
  claim: string;
  sourceUrl: string;
  reason: string;
  confidence: number;
}

export type ResearchEventPayload =
  | { kind: "conversation_identified"; conversationId: string }
  | { kind: "research_run_identified"; researchRunId: string }
  | { kind: "text_chunk"; text: string; isFinalChunk: boolean }
  | {
      kind: "graph_stage_started";
      stageName: string;
      stageIndex: number;
      detail: string;
    }
  | {
      kind: "graph_stage_ended";
      stageName: string;
      stageIndex: number;
      detail: string;
    }
  | {
      kind: "tool_started";
      executionId: string;
      toolName: string;
      arguments: Record<string, unknown>;
    }
  | {
      kind: "tool_ended";
      executionId: string;
      toolName: string;
      output: Record<string, unknown>;
      executionTimeMs: number;
      success: boolean;
    }
  | {
      kind: "source_discovered";
      sourceId: string;
      title: string;
      url: string;
      publisher: string;
    }
  | {
      kind: "evidence_accepted" | "evidence_rejected";
      evidenceId: string;
      claim: string;
      sourceUrl: string;
      reason: string;
      confidence: number;
    }
  | {
      kind: "research_gap_found";
      gapId: string;
      question: string;
      reportSection: string;
    }
  | {
      kind: "comparison_artifact";
      comparisonId: string;
      structuredResult: Record<string, unknown>;
    }
  | {
      kind: "final_report_artifact";
      researchRunId: string;
      reportMarkdown: string;
      confidenceScore: number;
      coverageScore: number;
    }
  | { kind: "error"; code: string; message: string; retryable: boolean }
  | { kind: "finished"; success: boolean };

export interface ResearchStreamEvent {
  eventId: string;
  timestamp: string;
  payload: ResearchEventPayload;
}

const streamEventType = protobuf.Root.fromJSON(schema).lookupType(
  "competitor_intelligence.streaming.v1.StreamEvent",
);

/** Decode and validate a base64 Protobuf research event. */
export function decodeResearchEvent(base64Data: string): ResearchStreamEvent {
  const bytes = Uint8Array.from(atob(base64Data), (character) =>
    character.charCodeAt(0),
  );
  const decoded = streamEventType.toObject(streamEventType.decode(bytes), {
    defaults: false,
    longs: Number,
  }) as unknown as WireEvent;
  return {
    eventId: decoded.eventId,
    timestamp: decoded.timestamp,
    payload: wirePayload(decoded),
  };
}

function wirePayload(event: WireEvent): ResearchEventPayload {
  if (event.conversationIdentified)
    return {
      kind: "conversation_identified",
      conversationId: event.conversationIdentified.conversationId,
    };
  if (event.researchRunIdentified)
    return {
      kind: "research_run_identified",
      researchRunId: event.researchRunIdentified.researchRunId,
    };
  if (event.textChunk) return { kind: "text_chunk", ...event.textChunk };
  if (event.graphStageStarted)
    return { kind: "graph_stage_started", ...event.graphStageStarted };
  if (event.graphStageEnded)
    return { kind: "graph_stage_ended", ...event.graphStageEnded };
  if (event.toolStarted)
    return {
      kind: "tool_started",
      executionId: event.toolStarted.executionId,
      toolName: event.toolStarted.toolName,
      arguments: parseObject(event.toolStarted.argumentsJson),
    };
  if (event.toolEnded)
    return {
      kind: "tool_ended",
      executionId: event.toolEnded.executionId,
      toolName: event.toolEnded.toolName,
      output: parseObject(event.toolEnded.outputJson),
      executionTimeMs: event.toolEnded.executionTimeMs,
      success: event.toolEnded.success,
    };
  if (event.sourceDiscovered)
    return { kind: "source_discovered", ...event.sourceDiscovered };
  if (event.evidenceAccepted)
    return { kind: "evidence_accepted", ...event.evidenceAccepted };
  if (event.evidenceRejected)
    return { kind: "evidence_rejected", ...event.evidenceRejected };
  if (event.researchGapFound)
    return { kind: "research_gap_found", ...event.researchGapFound };
  if (event.comparisonArtifact)
    return {
      kind: "comparison_artifact",
      comparisonId: event.comparisonArtifact.comparisonId,
      structuredResult: parseObject(
        event.comparisonArtifact.structuredResultJson,
      ),
    };
  if (event.finalReportArtifact)
    return { kind: "final_report_artifact", ...event.finalReportArtifact };
  if (event.error) return { kind: "error", ...event.error };
  if (event.finished) return { kind: "finished", ...event.finished };
  throw new Error("Protobuf event did not contain a supported payload");
}

function parseObject(value: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Expected an object encoded in the Protobuf JSON field");
  }
  return parsed as Record<string, unknown>;
}

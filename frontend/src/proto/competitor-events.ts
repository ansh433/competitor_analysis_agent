import type { INamespace } from "protobufjs";
import protobuf from "protobufjs/light";

const schema: INamespace = {
  nested: {
    competitor_intelligence: {
      nested: {
        streaming: {
          nested: {
            v1: {
              nested: {
                ConversationIdentified: { fields: { conversationId: { type: "string", id: 1 } } },
                ResearchRunIdentified: { fields: { researchRunId: { type: "string", id: 1 } } },
                TextChunk: {
                  fields: { text: { type: "string", id: 1 }, isFinalChunk: { type: "bool", id: 2 } },
                },
                GraphStageEvent: {
                  fields: {
                    stageName: { type: "string", id: 1 },
                    stageIndex: { type: "int32", id: 2 },
                    detail: { type: "string", id: 3 },
                  },
                },
                ToolStarted: {
                  fields: {
                    executionId: { type: "string", id: 1 },
                    toolName: { type: "string", id: 2 },
                    argumentsJson: { type: "string", id: 3 },
                  },
                },
                ToolEnded: {
                  fields: {
                    executionId: { type: "string", id: 1 },
                    toolName: { type: "string", id: 2 },
                    outputJson: { type: "string", id: 3 },
                    executionTimeMs: { type: "int64", id: 4 },
                    success: { type: "bool", id: 5 },
                  },
                },
                SourceDiscovered: {
                  fields: {
                    sourceId: { type: "string", id: 1 },
                    title: { type: "string", id: 2 },
                    url: { type: "string", id: 3 },
                    publisher: { type: "string", id: 4 },
                  },
                },
                EvidenceEvent: {
                  fields: {
                    evidenceId: { type: "string", id: 1 },
                    claim: { type: "string", id: 2 },
                    sourceUrl: { type: "string", id: 3 },
                    reason: { type: "string", id: 4 },
                    confidence: { type: "double", id: 5 },
                  },
                },
                ResearchGapFound: {
                  fields: {
                    gapId: { type: "string", id: 1 },
                    question: { type: "string", id: 2 },
                    reportSection: { type: "string", id: 3 },
                  },
                },
                ComparisonArtifact: {
                  fields: {
                    comparisonId: { type: "string", id: 1 },
                    structuredResultJson: { type: "string", id: 2 },
                  },
                },
                FinalReportArtifact: {
                  fields: {
                    researchRunId: { type: "string", id: 1 },
                    reportMarkdown: { type: "string", id: 2 },
                    confidenceScore: { type: "double", id: 3 },
                    coverageScore: { type: "double", id: 4 },
                  },
                },
                StreamError: {
                  fields: {
                    code: { type: "string", id: 1 },
                    message: { type: "string", id: 2 },
                    retryable: { type: "bool", id: 3 },
                  },
                },
                StreamFinished: { fields: { success: { type: "bool", id: 1 } } },
                StreamEvent: {
                  oneofs: {
                    payload: {
                      oneof: [
                        "conversationIdentified",
                        "researchRunIdentified",
                        "textChunk",
                        "graphStageStarted",
                        "graphStageEnded",
                        "toolStarted",
                        "toolEnded",
                        "sourceDiscovered",
                        "evidenceAccepted",
                        "evidenceRejected",
                        "researchGapFound",
                        "comparisonArtifact",
                        "finalReportArtifact",
                        "error",
                        "finished",
                      ],
                    },
                  },
                  fields: {
                    eventId: { type: "string", id: 1 },
                    timestamp: { type: "string", id: 2 },
                    conversationIdentified: { type: "ConversationIdentified", id: 3 },
                    researchRunIdentified: { type: "ResearchRunIdentified", id: 4 },
                    textChunk: { type: "TextChunk", id: 5 },
                    graphStageStarted: { type: "GraphStageEvent", id: 6 },
                    graphStageEnded: { type: "GraphStageEvent", id: 7 },
                    toolStarted: { type: "ToolStarted", id: 8 },
                    toolEnded: { type: "ToolEnded", id: 9 },
                    sourceDiscovered: { type: "SourceDiscovered", id: 10 },
                    evidenceAccepted: { type: "EvidenceEvent", id: 11 },
                    evidenceRejected: { type: "EvidenceEvent", id: 12 },
                    researchGapFound: { type: "ResearchGapFound", id: 13 },
                    comparisonArtifact: { type: "ComparisonArtifact", id: 14 },
                    finalReportArtifact: { type: "FinalReportArtifact", id: 15 },
                    error: { type: "StreamError", id: 16 },
                    finished: { type: "StreamFinished", id: 17 },
                  },
                },
              },
            },
          },
        },
      },
    },
  },
};

interface WireEvent {
  eventId: string;
  timestamp: string;
  conversationIdentified?: { conversationId: string };
  researchRunIdentified?: { researchRunId: string };
  textChunk?: { text: string; isFinalChunk: boolean };
  graphStageStarted?: { stageName: string; stageIndex: number; detail: string };
  graphStageEnded?: { stageName: string; stageIndex: number; detail: string };
  toolStarted?: { executionId: string; toolName: string; argumentsJson: string };
  toolEnded?: {
    executionId: string;
    toolName: string;
    outputJson: string;
    executionTimeMs: number;
    success: boolean;
  };
  sourceDiscovered?: { sourceId: string; title: string; url: string; publisher: string };
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
  | { kind: "graph_stage_started"; stageName: string; stageIndex: number; detail: string }
  | { kind: "graph_stage_ended"; stageName: string; stageIndex: number; detail: string }
  | { kind: "tool_started"; executionId: string; toolName: string; arguments: Record<string, unknown> }
  | { kind: "tool_ended"; executionId: string; toolName: string; output: Record<string, unknown>; executionTimeMs: number; success: boolean }
  | { kind: "source_discovered"; sourceId: string; title: string; url: string; publisher: string }
  | { kind: "evidence_accepted" | "evidence_rejected"; evidenceId: string; claim: string; sourceUrl: string; reason: string; confidence: number }
  | { kind: "research_gap_found"; gapId: string; question: string; reportSection: string }
  | { kind: "comparison_artifact"; comparisonId: string; structuredResult: Record<string, unknown> }
  | { kind: "final_report_artifact"; researchRunId: string; reportMarkdown: string; confidenceScore: number; coverageScore: number }
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
  const bytes = Uint8Array.from(atob(base64Data), (character) => character.charCodeAt(0));
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
  if (event.conversationIdentified) return { kind: "conversation_identified", conversationId: event.conversationIdentified.conversationId };
  if (event.researchRunIdentified) return { kind: "research_run_identified", researchRunId: event.researchRunIdentified.researchRunId };
  if (event.textChunk) return { kind: "text_chunk", ...event.textChunk };
  if (event.graphStageStarted) return { kind: "graph_stage_started", ...event.graphStageStarted };
  if (event.graphStageEnded) return { kind: "graph_stage_ended", ...event.graphStageEnded };
  if (event.toolStarted) return { kind: "tool_started", executionId: event.toolStarted.executionId, toolName: event.toolStarted.toolName, arguments: parseObject(event.toolStarted.argumentsJson) };
  if (event.toolEnded) return { kind: "tool_ended", executionId: event.toolEnded.executionId, toolName: event.toolEnded.toolName, output: parseObject(event.toolEnded.outputJson), executionTimeMs: event.toolEnded.executionTimeMs, success: event.toolEnded.success };
  if (event.sourceDiscovered) return { kind: "source_discovered", ...event.sourceDiscovered };
  if (event.evidenceAccepted) return { kind: "evidence_accepted", ...event.evidenceAccepted };
  if (event.evidenceRejected) return { kind: "evidence_rejected", ...event.evidenceRejected };
  if (event.researchGapFound) return { kind: "research_gap_found", ...event.researchGapFound };
  if (event.comparisonArtifact) return { kind: "comparison_artifact", comparisonId: event.comparisonArtifact.comparisonId, structuredResult: parseObject(event.comparisonArtifact.structuredResultJson) };
  if (event.finalReportArtifact) return { kind: "final_report_artifact", ...event.finalReportArtifact };
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


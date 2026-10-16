import base64
import json
import struct
from collections.abc import Iterable
from typing import Literal

from app.streaming.events import StreamEvent

WireType = Literal[0, 1, 2]

PAYLOAD_FIELD_NUMBERS = {
    "conversation_identified": 3,
    "research_run_identified": 4,
    "text_chunk": 5,
    "graph_stage_started": 6,
    "graph_stage_ended": 7,
    "tool_started": 8,
    "tool_ended": 9,
    "source_discovered": 10,
    "evidence_accepted": 11,
    "evidence_rejected": 12,
    "research_gap_found": 13,
    "comparison_artifact": 14,
    "final_report_artifact": 15,
    "error": 16,
    "finished": 17,
}


def encode_stream_event(event: StreamEvent) -> bytes:
    payload = event.payload
    envelope = bytearray()
    envelope.extend(_string_field(1, str(event.event_id)))
    envelope.extend(_string_field(2, event.timestamp.isoformat()))
    nested = _encode_payload(payload.kind, payload.model_dump(mode="json", exclude={"kind"}))
    envelope.extend(_bytes_field(PAYLOAD_FIELD_NUMBERS[payload.kind], nested))
    return bytes(envelope)


def encode_sse_event(event: StreamEvent) -> str:
    encoded = base64.b64encode(encode_stream_event(event)).decode("ascii")
    return f"id: {event.event_id}\nevent: {event.payload.kind}\ndata: {encoded}\n\n"


def encode_sse_stream(events: Iterable[StreamEvent]) -> Iterable[str]:
    for event in events:
        yield encode_sse_event(event)


def _encode_payload(kind: str, data: dict[str, object]) -> bytes:
    fields = bytearray()
    if kind == "conversation_identified":
        fields.extend(_string_field(1, str(data["conversation_id"])))
    elif kind == "research_run_identified":
        fields.extend(_string_field(1, str(data["research_run_id"])))
    elif kind == "text_chunk":
        fields.extend(_string_field(1, str(data["text"])))
        fields.extend(_varint_field(2, int(bool(data["is_final_chunk"]))))
    elif kind in {"graph_stage_started", "graph_stage_ended"}:
        fields.extend(_string_field(1, str(data["stage_name"])))
        fields.extend(_varint_field(2, int(data["stage_index"])))
        fields.extend(_string_field(3, str(data["detail"])))
    elif kind == "tool_started":
        fields.extend(_string_field(1, str(data["execution_id"])))
        fields.extend(_string_field(2, str(data["tool_name"])))
        fields.extend(_string_field(3, _json(data["arguments"])))
    elif kind == "tool_ended":
        fields.extend(_string_field(1, str(data["execution_id"])))
        fields.extend(_string_field(2, str(data["tool_name"])))
        fields.extend(_string_field(3, _json(data["output"])))
        fields.extend(_varint_field(4, int(data["execution_time_ms"])))
        fields.extend(_varint_field(5, int(bool(data["success"]))))
    elif kind == "source_discovered":
        for number, key in enumerate(("source_id", "title", "url", "publisher"), start=1):
            fields.extend(_string_field(number, str(data[key])))
    elif kind in {"evidence_accepted", "evidence_rejected"}:
        for number, key in enumerate(("evidence_id", "claim", "source_url", "reason"), start=1):
            fields.extend(_string_field(number, str(data[key])))
        fields.extend(_double_field(5, float(data["confidence"])))
    elif kind == "research_gap_found":
        for number, key in enumerate(("gap_id", "question", "report_section"), start=1):
            fields.extend(_string_field(number, str(data[key])))
    elif kind == "comparison_artifact":
        fields.extend(_string_field(1, str(data["comparison_id"])))
        fields.extend(_string_field(2, _json(data["structured_result"])))
    elif kind == "final_report_artifact":
        fields.extend(_string_field(1, str(data["research_run_id"])))
        fields.extend(_string_field(2, str(data["report_markdown"])))
        fields.extend(_double_field(3, float(data["confidence_score"])))
        fields.extend(_double_field(4, float(data["coverage_score"])))
    elif kind == "error":
        fields.extend(_string_field(1, str(data["code"])))
        fields.extend(_string_field(2, str(data["message"])))
        fields.extend(_varint_field(3, int(bool(data["retryable"]))))
    elif kind == "finished":
        fields.extend(_varint_field(1, int(bool(data["success"]))))
    else:
        raise ValueError(f"Unsupported stream payload: {kind}")
    return bytes(fields)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _key(field_number: int, wire_type: WireType) -> bytes:
    return _varint((field_number << 3) | wire_type)


def _varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("Protobuf varints must be nonnegative")
    encoded = bytearray()
    while value > 0x7F:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def _varint_field(field_number: int, value: int) -> bytes:
    return _key(field_number, 0) + _varint(value)


def _double_field(field_number: int, value: float) -> bytes:
    return _key(field_number, 1) + struct.pack("<d", value)


def _bytes_field(field_number: int, value: bytes) -> bytes:
    return _key(field_number, 2) + _varint(len(value)) + value


def _string_field(field_number: int, value: str) -> bytes:
    return _bytes_field(field_number, value.encode("utf-8"))

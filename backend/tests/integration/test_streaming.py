import pytest

from tests.client import IntegrationClient

pytestmark = pytest.mark.integration


def test_sse_stream_contains_typed_protobuf_sequence_and_persists_timeline(
    client: IntegrationClient,
    auth_headers: dict[str, str],
) -> None:
    conversation = client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"title": "Streaming research"},
    ).json()

    response = client.post(
        f"/api/v1/conversations/{conversation['id']}/responses",
        headers=auth_headers,
        json={"content": "Research Acme"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    event_names = [
        line.removeprefix("event: ")
        for line in response.text.splitlines()
        if line.startswith("event: ")
    ]
    assert event_names == [
        "conversation_identified",
        "graph_stage_started",
        "graph_stage_ended",
        "text_chunk",
        "finished",
    ]
    data_lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    assert len(data_lines) == 5
    assert all(len(line.removeprefix("data: ")) > 20 for line in data_lines)

    timeline = client.get(
        f"/api/v1/conversations/{conversation['id']}/events",
        headers=auth_headers,
    )
    assert timeline.status_code == 200
    assert [event["event_type"] for event in timeline.json()["events"]] == event_names

    detail = client.get(f"/api/v1/conversations/{conversation['id']}", headers=auth_headers).json()
    assert [message["sender"] for message in detail["messages"]] == ["user", "assistant"]
    assert len(detail["messages"][1]["structured_metadata"]["stream_event_ids"]) == 5

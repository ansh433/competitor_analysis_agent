import os

import pytest

from tests.client import IntegrationClient

pytestmark = pytest.mark.integration


def login_headers(client: IntegrationClient, credentials: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_conversation_persistence_rename_and_delete(
    client: IntegrationClient,
    auth_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"title": "Market entry thesis"},
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    message = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "Compare the collaboration software market."},
    )
    assert message.status_code == 201

    renamed = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers,
        json={"title": "Collaboration market thesis"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Collaboration market thesis"

    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["messages"][0]["content"].startswith("Compare")

    deleted = client.delete(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert (
        client.get(f"/api/v1/conversations/{conversation_id}", headers=auth_headers).status_code
        == 404
    )


def test_conversations_are_tenant_isolated(
    client: IntegrationClient,
    auth_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"title": "Private strategy"},
    )
    conversation_id = created.json()["id"]

    other_credentials = {
        "email": f"other-{os.urandom(4).hex()}@example.com",
        "password": "another correct research password",
        "full_name": "Other Analyst",
    }
    assert client.post("/api/v1/auth/register", json=other_credentials).status_code == 201
    other_headers = login_headers(client, other_credentials)

    assert (
        client.get(f"/api/v1/conversations/{conversation_id}", headers=other_headers).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/conversations/{conversation_id}",
            headers=other_headers,
            json={"title": "Stolen"},
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/v1/conversations/{conversation_id}", headers=other_headers).status_code
        == 404
    )


def test_conversation_branch_copies_history_through_selected_message(
    client: IntegrationClient,
    auth_headers: dict[str, str],
) -> None:
    conversation = client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"title": "Original hypothesis"},
    ).json()
    first = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_headers,
        json={"content": "First hypothesis"},
    ).json()
    client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_headers,
        json={"content": "Later hypothesis"},
    )

    branch = client.post(
        f"/api/v1/conversations/{conversation['id']}/branches",
        headers=auth_headers,
        json={"origin_message_id": first["id"], "title": "Alternative hypothesis"},
    )

    assert branch.status_code == 201
    assert branch.json()["parent_conversation_id"] == conversation["id"]
    assert branch.json()["branch_origin_message_id"] == first["id"]
    assert [message["content"] for message in branch.json()["messages"]] == ["First hypothesis"]

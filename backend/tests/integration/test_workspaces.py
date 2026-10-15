import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_workspace_and_company_lifecycle(client: TestClient, auth_headers: dict[str, str]) -> None:
    workspace = client.post(
        "/api/v1/workspaces",
        headers=auth_headers,
        json={"name": "Launch strategy", "description": "Entry assessment"},
    )
    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]
    company = client.post(
        f"/api/v1/workspaces/{workspace_id}/companies",
        headers=auth_headers,
        json={"display_name": "Acme", "website": "https://acme.example/products"},
    )
    assert company.status_code == 201
    assert company.json()["domain"] == "acme.example"
    company_id = company.json()["id"]

    assert client.put(
        f"/api/v1/companies/{company_id}/tracking",
        headers=auth_headers,
        json={"monitoring_preferences": {"news": True}},
    ).status_code == 200
    assert len(client.get("/api/v1/tracked-companies", headers=auth_headers).json()["tracked_companies"]) >= 1
    assert client.patch(
        f"/api/v1/companies/{company_id}",
        headers=auth_headers,
        json={"industry": "Collaboration software"},
    ).json()["industry"] == "Collaboration software"
    assert client.delete(f"/api/v1/workspaces/{workspace_id}", headers=auth_headers).status_code == 204


def test_workspace_and_company_queries_are_tenant_isolated(client: TestClient, auth_headers: dict[str, str]) -> None:
    workspace = client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"name": "Confidential"}
    ).json()
    company = client.post(
        f"/api/v1/workspaces/{workspace['id']}/companies",
        headers=auth_headers,
        json={"display_name": "Private Company"},
    ).json()
    other = {
        "email": f"workspace-{os.urandom(4).hex()}@example.com",
        "password": "separate tenant research password",
        "full_name": "Second Tenant",
    }
    assert client.post("/api/v1/auth/register", json=other).status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": other["email"], "password": other["password"]})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert client.get(f"/api/v1/workspaces/{workspace['id']}", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/companies/{company['id']}", headers=other_headers).status_code == 404
    assert client.get(
        f"/api/v1/workspaces/{workspace['id']}/companies", headers=other_headers
    ).status_code == 404


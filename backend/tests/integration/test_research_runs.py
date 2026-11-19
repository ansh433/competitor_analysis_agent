import os

import pytest

from app.core.errors import ExternalProviderError, RetryableExternalProviderError
from app.providers.base import ResearchProviders, ResponseModel
from app.providers.deterministic import (
    DeterministicModelProvider,
    DeterministicPageFetcher,
    DeterministicSearchProvider,
)
from tests.client import IntegrationClient

pytestmark = pytest.mark.integration


def create_user_headers(client: IntegrationClient, prefix: str) -> dict[str, str]:
    credentials = {
        "email": f"{prefix}-{os.urandom(4).hex()}@example.com",
        "password": "integrated competitor research password",
        "full_name": f"{prefix.title()} Analyst",
    }
    assert client.post("/api/v1/auth/register", json=credentials).status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_workspace(client: IntegrationClient, headers: dict[str, str], name: str) -> str:
    response = client.post("/api/v1/workspaces", headers=headers, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def create_run(
    client: IntegrationClient,
    headers: dict[str, str],
    workspace_id: str,
    company: str = "Acme Collaboration",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/research-runs",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "company_name_or_url": company,
            "objective": "Assess product differentiation and competitive positioning for market entry.",
            "model_tier": "standard",
        },
    )
    assert response.status_code == 201
    return response.json()


def event_names(stream_body: str) -> list[str]:
    return [
        line.removeprefix("event: ")
        for line in stream_body.splitlines()
        if line.startswith("event: ")
    ]


def test_full_research_stream_persists_verified_dossier_and_artifacts(
    client: IntegrationClient,
) -> None:
    headers = create_user_headers(client, "full-run")
    workspace_id = create_workspace(client, headers, "Full research")
    before = client.get("/api/v1/quotas/me", headers=headers).json()
    research_run = create_run(client, headers, workspace_id)
    after = client.get("/api/v1/quotas/me", headers=headers).json()
    assert after["tiers"][0]["used"] == before["tiers"][0]["used"] + 1

    stream = client.post(f"/api/v1/research-runs/{research_run['id']}/stream", headers=headers)
    assert stream.status_code == 200
    names = event_names(stream.text)
    assert names[0:2] == ["conversation_identified", "research_run_identified"]
    assert "graph_stage_started" in names
    assert "tool_started" in names
    assert "tool_ended" in names
    assert "source_discovered" in names
    assert "evidence_accepted" in names
    assert "research_gap_found" in names
    assert "comparison_artifact" in names
    assert "final_report_artifact" in names
    assert names[-1] == "finished"

    detail = client.get(f"/api/v1/research-runs/{research_run['id']}", headers=headers)
    assert detail.status_code == 200
    artifact = detail.json()
    assert artifact["status"] == "completed"
    assert len(artifact["evidence"]) >= 5
    assert artifact["comparison_id"]
    assert "## 15. Evidence ledger" in artifact["final_report"]
    assert "## 16. Coverage and confidence" in artifact["final_report"]
    for evidence in artifact["evidence"]:
        assert f"/api/v1/evidence/{evidence['id']}" in artifact["final_report"]
        assert evidence["verification_status"] == "accepted"

    comparison = client.get(f"/api/v1/comparisons/{artifact['comparison_id']}", headers=headers)
    assert comparison.status_code == 200
    assert comparison.json()["structured_result"]["rows"]
    timeline = client.get(
        f"/api/v1/conversations/{research_run['conversation_id']}/events",
        headers=headers,
    )
    assert timeline.status_code == 200
    persisted_types = [item["event_type"] for item in timeline.json()["events"]]
    assert "tool_started" in persisted_types
    assert "graph_stage_ended" in persisted_types
    gap_stage_count = sum(
        1
        for item in timeline.json()["events"]
        if item["event_type"] == "graph_stage_started"
        and item["payload"].get("stage_name") == "targeted_gap_research"
    )
    assert gap_stage_count == 2


def test_reports_evidence_and_comparisons_are_tenant_isolated(
    client: IntegrationClient,
) -> None:
    owner_headers = create_user_headers(client, "owner")
    workspace_id = create_workspace(client, owner_headers, "Owner workspace")
    research_run = create_run(client, owner_headers, workspace_id)
    client.post(f"/api/v1/research-runs/{research_run['id']}/stream", headers=owner_headers)
    artifact = client.get(
        f"/api/v1/research-runs/{research_run['id']}", headers=owner_headers
    ).json()
    outsider_headers = create_user_headers(client, "outsider")

    assert (
        client.get(
            f"/api/v1/research-runs/{research_run['id']}", headers=outsider_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/evidence/{artifact['evidence'][0]['id']}", headers=outsider_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/comparisons/{artifact['comparison_id']}", headers=outsider_headers
        ).status_code
        == 404
    )


def test_standard_research_quota_is_enforced(client: IntegrationClient) -> None:
    headers = create_user_headers(client, "quota")
    workspace_id = create_workspace(client, headers, "Quota workspace")
    quota = client.get("/api/v1/quotas/me", headers=headers).json()
    standard_limit = next(item["limit"] for item in quota["tiers"] if item["tier"] == "standard")
    for index in range(standard_limit):
        create_run(client, headers, workspace_id, company=f"Quota Company {index}")

    exhausted = client.post(
        "/api/v1/research-runs",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "company_name_or_url": "One Company Too Many",
            "objective": "Assess this company after the daily allowance has already been exhausted.",
            "model_tier": "standard",
        },
    )
    assert exhausted.status_code == 429
    assert exhausted.json()["error"]["code"] == "quota_exceeded"


def test_provider_failure_marks_run_failed_and_streams_typed_error(
    client: IntegrationClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_provider_build(*_args: object, **_kwargs: object) -> object:
        raise ExternalProviderError("deterministic provider failure")

    monkeypatch.setattr(
        "app.research.stream_runner.build_research_providers",
        fail_provider_build,
    )
    headers = create_user_headers(client, "failure")
    workspace_id = create_workspace(client, headers, "Failure workspace")
    research_run = create_run(client, headers, workspace_id)

    stream = client.post(f"/api/v1/research-runs/{research_run['id']}/stream", headers=headers)
    assert event_names(stream.text) == ["error", "finished"]
    detail = client.get(f"/api/v1/research-runs/{research_run['id']}", headers=headers)
    assert detail.json()["status"] == "failed"
    assert detail.json()["error_message"].startswith("ExternalProviderError")


def test_targeted_fetch_failure_is_rejected_without_failing_research_run(
    client: IntegrationClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailOneTargetedFetch(DeterministicPageFetcher):
        def fetch(self, url: str):
            if "enterprise+pricing" in url:
                raise ExternalProviderError("targeted source blocked")
            return super().fetch(url)

    providers = ResearchProviders(
        search=DeterministicSearchProvider(),
        pages=FailOneTargetedFetch(),
        model=DeterministicModelProvider(),
    )
    monkeypatch.setattr(
        "app.research.stream_runner.build_research_providers",
        lambda *_args, **_kwargs: providers,
    )
    headers = create_user_headers(client, "targeted-fetch-failure")
    workspace_id = create_workspace(client, headers, "Targeted fetch failure")
    research_run = create_run(client, headers, workspace_id)

    stream = client.post(f"/api/v1/research-runs/{research_run['id']}/stream", headers=headers)

    assert stream.status_code == 200
    assert "evidence_rejected" in event_names(stream.text)
    detail = client.get(f"/api/v1/research-runs/{research_run['id']}", headers=headers)
    assert detail.json()["status"] == "completed"
    assert all("enterprise+pricing" not in item["source_url"] for item in detail.json()["evidence"])


def test_retryable_provider_failure_pauses_and_resumes_from_checkpoint(
    client: IntegrationClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailCompetitorDiscoveryOnce(DeterministicModelProvider):
        failed = False

        def generate_structured(
            self,
            system_prompt: str,
            user_prompt: str,
            schema: type[ResponseModel],
            *,
            task_name: str | None = None,
        ) -> ResponseModel:
            if schema.__name__ == "CompetitorDiscovery" and not self.failed:
                self.failed = True
                raise RetryableExternalProviderError("temporary competitor discovery limit")
            return super().generate_structured(
                system_prompt,
                user_prompt,
                schema,
                task_name=task_name,
            )

    providers = ResearchProviders(
        search=DeterministicSearchProvider(),
        pages=DeterministicPageFetcher(),
        model=FailCompetitorDiscoveryOnce(),
    )
    monkeypatch.setattr(
        "app.research.stream_runner.build_research_providers",
        lambda *_args, **_kwargs: providers,
    )
    headers = create_user_headers(client, "resume")
    workspace_id = create_workspace(client, headers, "Resume workspace")
    quota_before = client.get("/api/v1/quotas/me", headers=headers).json()
    research_run = create_run(client, headers, workspace_id)

    first_stream = client.post(
        f"/api/v1/research-runs/{research_run['id']}/stream",
        headers=headers,
    )
    assert "error" in event_names(first_stream.text)
    paused = client.get(f"/api/v1/research-runs/{research_run['id']}", headers=headers).json()
    assert paused["status"] == "paused"
    assert paused["resume_stage"] == "create_research_plan"
    assert paused["checkpoint_version"] > 0

    resumed_stream = client.post(
        f"/api/v1/research-runs/{research_run['id']}/resume",
        headers=headers,
    )
    assert resumed_stream.status_code == 200
    assert "final_report_artifact" in event_names(resumed_stream.text)
    completed = client.get(f"/api/v1/research-runs/{research_run['id']}", headers=headers).json()
    assert completed["status"] == "completed"
    assert completed["resume_count"] == 1
    assert completed["resume_stage"] is None
    assert "## 15. Evidence ledger" in completed["final_report"]

    quota_after = client.get("/api/v1/quotas/me", headers=headers).json()
    before_used = next(item["used"] for item in quota_before["tiers"] if item["tier"] == "standard")
    after_used = next(item["used"] for item in quota_after["tiers"] if item["tier"] == "standard")
    assert after_used == before_used + 1


def test_long_conversation_persists_summary_before_research(
    client: IntegrationClient,
) -> None:
    headers = create_user_headers(client, "context")
    workspace_id = create_workspace(client, headers, "Context workspace")
    conversation = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Long competitive hypothesis"},
    ).json()
    for index in range(18):
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=headers,
            json={
                "content": (
                    f"Turn {index}: compare Acme Collaboration pricing, positioning, "
                    "and enterprise workflow evidence."
                )
            },
        )
        assert response.status_code == 201
    run = client.post(
        "/api/v1/research-runs",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "conversation_id": conversation["id"],
            "company_name_or_url": "Acme Collaboration",
            "objective": "Reassess the earlier Acme enterprise pricing and positioning hypothesis.",
            "model_tier": "standard",
        },
    ).json()
    assert (
        client.post(f"/api/v1/research-runs/{run['id']}/stream", headers=headers).status_code == 200
    )
    detail = client.get(f"/api/v1/conversations/{conversation['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["summary"]

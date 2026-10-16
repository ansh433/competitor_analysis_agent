from uuid import uuid4

import pytest

from app.agent.state import ResearchGraphContext
from app.agent.workflow import COMPETITOR_RESEARCH_GRAPH
from app.providers.base import ResearchProviders
from app.providers.deterministic import (
    DeterministicModelProvider,
    DeterministicPageFetcher,
    DeterministicSearchProvider,
)
from app.research_tools.context import ResearchToolContext
from app.streaming.events import StreamPayload

pytestmark = pytest.mark.integration


def test_explicit_state_graph_runs_parallel_research_and_bounded_gap_loop() -> None:
    user_id = uuid4()
    workspace_id = uuid4()
    conversation_id = uuid4()
    run_id = uuid4()
    emitted: list[StreamPayload] = []
    providers = ResearchProviders(
        search=DeterministicSearchProvider(),
        pages=DeterministicPageFetcher(),
        model=DeterministicModelProvider(),
    )
    context = ResearchGraphContext(
        tools=ResearchToolContext(
            user_id=user_id,
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            research_run_id=run_id,
            providers=providers,
            maximum_sources=20,
        ),
        emit=emitted.append,
    )

    result = COMPETITOR_RESEARCH_GRAPH.invoke(
        {
            "authenticated_user_id": user_id,
            "workspace_id": workspace_id,
            "conversation_id": conversation_id,
            "research_run_id": run_id,
            "research_objective": "Assess competitive positioning for a product strategy decision.",
            "company_input": "Acme Collaboration",
            "loop_count": 0,
            "maximum_gap_loops": 1,
        },
        context=context,
    )

    assert result["canonical_company"].canonical_name == "Acme Collaboration"
    assert len(result["competitor_research"]) == 2
    assert result["comparison_matrix"].rows
    assert result["loop_count"] == 1
    assert result["verification_results"].passed is True
    assert result["final_artifact"]["research_run_id"] == str(run_id)
    starts = [event for event in emitted if event.kind == "tool_started"]
    ends = [event for event in emitted if event.kind == "tool_ended"]
    assert len(starts) == len(ends)
    assert all(event.execution_time_ms >= 0 for event in ends)

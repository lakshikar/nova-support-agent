from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.graph import LangGraphSupportAgent
from domain.entities.models import (
    InvestigationPlan,
    InvestigationStep,
    SupportTicket,
    TicketUnderstanding,
)
from domain.value_objects.enums import Severity, SupportTier
from infrastructure.config.settings import Settings


class FakeLLM:
    async def invoke(self, prompt: str, system: str | None = None) -> str:
        return '{"evidence_sufficient": true, "reason": "enough evidence"}'

    async def invoke_structured(self, prompt: str, schema: type, system: str | None = None):
        if schema is TicketUnderstanding:
            return TicketUnderstanding(
                affected_module="asset-lifecycle",
                error_codes=["NT-4523"],
                support_tier=SupportTier.PREMIUM,
                severity=Severity.HIGH,
                urgency_rationale="Report generation blocked",
            )
        if schema is InvestigationPlan:
            return InvestigationPlan(
                strategy_summary="Search docs",
                steps=[
                    InvestigationStep(
                        tool="lookup_ticket_history",
                        rationale="Find similar tickets",
                        parameters={"query": "NT-4523"},
                    )
                ],
            )
        if schema.__name__ == "ResolutionReport":
            from domain.entities.models import (
                EscalationRecommendation,
                ResolutionReport,
            )
            from domain.value_objects.enums import ConfidenceLevel

            return ResolutionReport(
                request_id="test-id",
                diagnosis="NT-4523 depreciation report failure",
                recommended_resolution=["Use legacy endpoint"],
                confidence_level=ConfidenceLevel.HIGH,
                confidence_rationale="Exact match",
                escalation_recommendation=EscalationRecommendation(
                    required=False,
                    reason="Workaround available",
                ),
            )
        raise ValueError(f"Unexpected schema: {schema}")


class FakeMCP:
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        if tool_name == "lookup_ticket_history":
            return {"tickets": [{"ticketId": "TK-20235"}], "access_denied": False}
        if tool_name == "check_sla_policy":
            return {"responseSlaHours": 4.0}
        if tool_name == "search_documentation":
            return {"results": [{"source_file": "troubleshooting-guide.md", "content": "NT-4523"}]}
        return {}


class FakeLogger:
    def log_decision(self, *args, **kwargs) -> None:
        pass

    def log_tool_call(self, *args, **kwargs) -> None:
        pass


@pytest.fixture
def ticket() -> SupportTicket:
    return SupportTicket(
        subject="Error NT-4523 when generating asset report",
        body="Quarterly depreciation report fails after v24.2 upgrade.",
        customer="Meridian Energy",
        supportTier=SupportTier.PREMIUM,
        createdAt=datetime(2024, 5, 20, 9, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_agent_guardrails_add_search_and_sla(ticket: SupportTicket) -> None:
    agent = LangGraphSupportAgent(FakeLLM(), FakeMCP(), Settings(max_agent_iterations=3))
    plan = InvestigationPlan(
        strategy_summary="Minimal plan",
        steps=[
            InvestigationStep(
                tool="lookup_ticket_history",
                rationale="History",
                parameters={"query": "NT-4523"},
            )
        ],
    )
    understanding = TicketUnderstanding(
        error_codes=["NT-4523"],
        support_tier=SupportTier.PREMIUM,
        severity=Severity.HIGH,
    )
    result = agent._apply_guardrails(plan, understanding, ticket)
    tools = [step.tool for step in result.steps]
    assert "search_documentation" in tools
    assert "check_sla_policy" in tools


@pytest.mark.asyncio
async def test_agent_investigate_produces_report(ticket: SupportTicket) -> None:
    agent = LangGraphSupportAgent(FakeLLM(), FakeMCP(), Settings(max_agent_iterations=3))
    report = await agent.investigate(ticket, "req-1", FakeLogger())
    assert "NT-4523" in report.diagnosis
    assert report.confidence_level.value == "high"

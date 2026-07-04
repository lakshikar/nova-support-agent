from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain.entities.models import (
    EscalationRecommendation,
    InvestigationPlan,
    InvestigationStep,
    ResolutionReport,
    SupportTicket,
    TicketUnderstanding,
)
from domain.value_objects.enums import ConfidenceLevel, Severity, SupportTier


def test_support_ticket_accepts_camel_case_aliases() -> None:
    ticket = SupportTicket.model_validate(
        {
            "subject": "Error NT-4523",
            "body": "Report fails",
            "customer": "Meridian Energy",
            "supportTier": "premium",
            "createdAt": "2024-05-20T09:00:00Z",
            "ticketReferences": ["TK-20251"],
        }
    )
    assert ticket.support_tier == SupportTier.PREMIUM
    assert ticket.ticket_references == ["TK-20251"]
    assert ticket.created_at is not None


def test_support_ticket_rejects_invalid_tier() -> None:
    with pytest.raises(ValidationError):
        SupportTicket.model_validate(
            {
                "subject": "Test",
                "body": "Test",
                "customer": "Acme",
                "supportTier": "gold",
            }
        )


def test_investigation_plan_tracks_steps() -> None:
    plan = InvestigationPlan(
        strategy_summary="Search docs for error code",
        steps=[
            InvestigationStep(
                tool="search_documentation",
                rationale="Error NT-4523 mentioned",
                parameters={"query": "NT-4523"},
            )
        ],
    )
    assert len(plan.steps) == 1
    assert plan.steps[0].completed is False


def test_ticket_understanding_defaults() -> None:
    understanding = TicketUnderstanding(
        support_tier=SupportTier.STANDARD,
        severity=Severity.HIGH,
    )
    assert understanding.error_codes == []
    assert understanding.is_ambiguous is False


def test_resolution_report_requires_core_fields() -> None:
    report = ResolutionReport(
        request_id="abc-123",
        diagnosis="Known issue NT-4523",
        recommended_resolution=["Use legacy endpoint"],
        confidence_level=ConfidenceLevel.HIGH,
        confidence_rationale="Exact error code match in docs",
        escalation_recommendation=EscalationRecommendation(
            required=False,
            reason="Workaround available",
        ),
    )
    assert report.confidence_level == ConfidenceLevel.HIGH

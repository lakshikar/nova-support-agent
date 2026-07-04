from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.config.settings import Settings
from mcp_server.tools.registry import DateCalculatorService, SLAPolicyService, TicketHistoryService


@pytest.fixture
def ticket_service(tmp_path: Path) -> TicketHistoryService:
    tickets = [
        {
            "ticketId": "TK-100",
            "subject": "Atlas issue",
            "body": "Sync failure",
            "customer": "Atlas Manufacturing",
            "status": "open",
            "tags": ["sync"],
            "resolution": None,
        },
        {
            "ticketId": "TK-200",
            "subject": "Other customer issue",
            "body": "Problem",
            "customer": "Meridian Energy",
            "status": "open",
            "tags": [],
            "resolution": None,
        },
    ]
    path = tmp_path / "tickets.json"
    path.write_text(json.dumps(tickets), encoding="utf-8")
    return TicketHistoryService(str(path))


def test_ticket_lookup_returns_customer_tickets(ticket_service: TicketHistoryService) -> None:
    result = ticket_service.lookup(customer="Atlas Manufacturing")
    assert len(result["tickets"]) == 1
    assert result["tickets"][0]["ticketId"] == "TK-100"
    assert result["access_denied"] is False


def test_ticket_lookup_blocks_cross_customer_access(ticket_service: TicketHistoryService) -> None:
    result = ticket_service.lookup(customer="Atlas Manufacturing", ticket_id="TK-200")
    assert result["tickets"] == []
    assert result["access_denied"] is True


def test_sla_policy_standard_high() -> None:
    service = SLAPolicyService()
    result = service.check(
        support_tier="standard",
        severity="high",
        ticket_created_at="2024-05-20T09:00:00Z",
    )
    assert result["responseSlaHours"] == 8.0
    assert result["resolutionSlaBusinessDays"] == 10


def test_date_calculator_business_hours_remaining() -> None:
    service = DateCalculatorService()
    result = service.calculate(
        operation="business_hours_remaining",
        start="2024-05-20T09:00:00Z",
        end="2024-05-20T13:00:00Z",
    )
    assert result["unit"] == "business_hours"
    assert result["result"] == pytest.approx(4.0)

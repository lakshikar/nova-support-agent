from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from domain.entities.models import (
    EscalationRecommendation,
    ResolutionReport,
    SupportTicket,
)
from domain.value_objects.enums import ConfidenceLevel
from infrastructure.config.settings import Settings
from infrastructure.logging.file_request_logger import FileRequestLogger


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    monkeypatch.setenv("LOGS_PATH", str(tmp_path / "logs"))
    from api import dependencies

    for fn in (
        dependencies.get_settings,
        dependencies.get_llm_provider,
        dependencies.get_vector_store,
        dependencies.get_document_repository,
        dependencies.get_tool_registry,
        dependencies.get_mcp_client,
        dependencies.get_request_logger,
        dependencies.get_support_agent,
    ):
        fn.cache_clear()

    mock_report = ResolutionReport(
        request_id="test-req",
        diagnosis="Test diagnosis",
        recommended_resolution=["Step 1"],
        confidence_level=ConfidenceLevel.HIGH,
        confidence_rationale="Test",
        escalation_recommendation=EscalationRecommendation(required=False, reason="None"),
    )

    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(return_value=mock_report)

    async def noop_ingest(force: bool = False) -> int:
        return 0

    mock_ingest = MagicMock()
    mock_ingest.execute = AsyncMock(side_effect=noop_ingest)

    monkeypatch.setattr(dependencies, "get_investigate_use_case", lambda: mock_use_case)
    monkeypatch.setattr(dependencies, "get_ingest_use_case", lambda: mock_ingest)
    monkeypatch.setattr(
        dependencies,
        "get_request_logger",
        lambda: FileRequestLogger(Settings(logs_path=str(tmp_path / "logs"))),
    )

    from api.main import app

    return TestClient(app, raise_server_exceptions=True)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_investigate_endpoint(client: TestClient) -> None:
    payload = {
        "subject": "Error NT-4523 when generating asset report",
        "body": "Report fails after v24.2 upgrade",
        "customer": "Meridian Energy",
        "supportTier": "premium",
        "createdAt": datetime(2024, 5, 20, 9, 0, tzinfo=timezone.utc).isoformat(),
    }
    response = client.post("/api/v1/investigate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "report" in data
    assert data["report"]["diagnosis"] == "Test diagnosis"
    assert "logPath" in data

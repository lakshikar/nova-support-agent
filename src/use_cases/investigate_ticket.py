from __future__ import annotations

import time

from domain.entities.models import ResolutionReport, SupportTicket
from domain.ports import RequestLogger
from domain.ports.support_agent import SupportAgent


class InvestigateTicketUseCase:
    """Application use case: investigate a support ticket."""

    def __init__(self, agent: SupportAgent, logger: RequestLogger) -> None:
        self._agent = agent
        self._logger = logger

    async def execute(self, ticket: SupportTicket, request_id: str) -> ResolutionReport:
        self._logger.start_request(request_id, ticket.model_dump(mode="json", by_alias=True))
        start = time.perf_counter()
        report = await self._agent.investigate(ticket, request_id, self._logger)
        elapsed = int((time.perf_counter() - start) * 1000)
        self._logger.complete_request(request_id, report, elapsed)
        return report

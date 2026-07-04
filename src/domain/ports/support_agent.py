from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import uuid4

from domain.entities.models import ResolutionReport, SupportTicket
from domain.ports import RequestLogger


class SupportAgent(ABC):
    """Port for the investigation agent orchestrator."""

    @abstractmethod
    async def investigate(
        self,
        ticket: SupportTicket,
        request_id: str,
        logger: RequestLogger,
    ) -> ResolutionReport:
        """Run full investigation pipeline and return structured report."""


def new_request_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

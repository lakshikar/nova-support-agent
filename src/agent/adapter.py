from __future__ import annotations

from agent.graph import LangGraphSupportAgent
from domain.entities.models import ResolutionReport, SupportTicket
from domain.ports import LLMProvider, MCPToolClient, RequestLogger
from domain.ports.support_agent import SupportAgent
from infrastructure.config.settings import Settings


class LangGraphSupportAgentAdapter(SupportAgent):
    def __init__(
        self,
        llm: LLMProvider,
        mcp_client: MCPToolClient,
        settings: Settings,
    ) -> None:
        self._agent = LangGraphSupportAgent(llm, mcp_client, settings)

    async def investigate(
        self,
        ticket: SupportTicket,
        request_id: str,
        logger: RequestLogger,
    ) -> ResolutionReport:
        return await self._agent.investigate(ticket, request_id, logger)

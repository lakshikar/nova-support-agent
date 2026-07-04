from __future__ import annotations

from typing import Any

from domain.ports import MCPToolClient
from mcp_server.tools.registry import ToolRegistry


class DirectMCPToolClient(MCPToolClient):
    """In-process MCP tool client using shared ToolRegistry."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def call_tool(self, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        result = await self._registry.call_tool(tool_name, dict(arguments))
        return result

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp.server.fastmcp import FastMCP

from infrastructure.config.settings import get_settings
from infrastructure.documents.markdown_repository import MarkdownDocumentRepository
from infrastructure.llm.embeddings import create_embedding_provider
from infrastructure.vector_store.pgvector_store import PgVectorStore
from mcp_server.tools.registry import ToolRegistry
from use_cases.ingest_documents import IngestDocumentsUseCase

mcp = FastMCP("NovaTech Support Tools")


def _get_registry() -> ToolRegistry:
    settings = get_settings()
    return ToolRegistry(
        settings,
        vector_store=PgVectorStore(settings),
        embedding_provider=create_embedding_provider(settings),
    )


@mcp.tool()
async def search_documentation(
    query: str,
    top_k: int = 5,
    source_filter: str | None = None,
) -> dict[str, object]:
    """Search NovaTech documentation for troubleshooting steps and known issues."""
    registry = _get_registry()
    return await registry.call_tool(
        "search_documentation",
        {"query": query, "top_k": top_k, "source_filter": source_filter},
    )


@mcp.tool()
async def lookup_ticket_history(
    customer: str,
    ticket_id: str | None = None,
    query: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, object]:
    """Search past support tickets scoped to the given customer."""
    registry = _get_registry()
    return await registry.call_tool(
        "lookup_ticket_history",
        {
            "customer": customer,
            "ticket_id": ticket_id,
            "query": query,
            "tags": tags or [],
        },
    )


@mcp.tool()
async def check_sla_policy(
    support_tier: str,
    severity: str,
    ticket_created_at: str,
) -> dict[str, object]:
    """Determine SLA response/resolution deadlines and escalation rules."""
    registry = _get_registry()
    return await registry.call_tool(
        "check_sla_policy",
        {
            "support_tier": support_tier,
            "severity": severity,
            "ticket_created_at": ticket_created_at,
        },
    )


@mcp.tool()
async def calculate_datetime(
    operation: str,
    start: str,
    end: str | None = None,
    hours: float = 0.0,
) -> dict[str, object]:
    """Compute business hours remaining, add hours, or diff between datetimes."""
    registry = _get_registry()
    return await registry.call_tool(
        "calculate_datetime",
        {"operation": operation, "start": start, "end": end, "hours": hours},
    )


async def _ensure_ingested() -> None:
    settings = get_settings()
    vector_store = PgVectorStore(settings)
    ingest = IngestDocumentsUseCase(
        MarkdownDocumentRepository(),
        create_embedding_provider(settings),
        vector_store,
        settings,
    )
    await ingest.execute(force=False)


if __name__ == "__main__":
    asyncio.run(_ensure_ingested())
    mcp.run(transport="sse")

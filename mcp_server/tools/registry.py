from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from domain.entities.models import DocumentChunk
from domain.ports import EmbeddingProvider, VectorStore
from infrastructure.config.settings import Settings


class TicketHistoryService:
    """Customer-scoped ticket history lookup."""

    def __init__(self, ticket_history_path: str) -> None:
        self._path = Path(ticket_history_path)
        self._tickets: list[dict[str, Any]] = json.loads(
            self._path.read_text(encoding="utf-8")
        )

    def lookup(
        self,
        customer: str,
        ticket_id: str | None = None,
        query: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        customer_lower = customer.lower()
        results: list[dict[str, Any]] = []

        for ticket in self._tickets:
            ticket_customer = str(ticket.get("customer", "")).lower()
            if ticket_id:
                if ticket.get("ticketId") != ticket_id:
                    continue
                if ticket_customer != customer_lower:
                    return {"tickets": [], "access_denied": True, "reason": "Customer scope mismatch"}
            elif ticket_customer != customer_lower:
                continue

            if query:
                haystack = " ".join(
                    [
                        str(ticket.get("subject", "")),
                        str(ticket.get("body", "")),
                        " ".join(ticket.get("tags", [])),
                    ]
                ).lower()
                if query.lower() not in haystack:
                    continue

            if tags:
                ticket_tags = {t.lower() for t in ticket.get("tags", [])}
                if not any(tag.lower() in ticket_tags for tag in tags):
                    continue

            results.append(
                {
                    "ticketId": ticket.get("ticketId"),
                    "subject": ticket.get("subject"),
                    "body": ticket.get("body"),
                    "status": ticket.get("status"),
                    "severity": ticket.get("severity"),
                    "module": ticket.get("module"),
                    "resolution": ticket.get("resolution"),
                    "tags": ticket.get("tags", []),
                    "relatedKnownIssue": ticket.get("relatedKnownIssue"),
                    "createdDate": ticket.get("createdDate"),
                }
            )

        return {"tickets": results, "access_denied": False}


class SLAPolicyService:
    """SLA deadline calculation from tier and severity."""

    RESPONSE_HOURS = {
        ("standard", "critical"): 8,
        ("standard", "high"): 8,
        ("standard", "medium"): 16,
        ("standard", "low"): 40,
        ("premium", "critical"): 2,
        ("premium", "high"): 4,
        ("premium", "medium"): 8,
        ("premium", "low"): 16,
    }

    RESOLUTION_BUSINESS_DAYS = {
        ("standard", "critical"): 5,
        ("standard", "high"): 10,
        ("standard", "medium"): 15,
        ("standard", "low"): 30,
        ("premium", "critical"): 2,
        ("premium", "high"): 5,
        ("premium", "medium"): 8,
        ("premium", "low"): 15,
    }

    def check(
        self,
        support_tier: str,
        severity: str,
        ticket_created_at: str,
    ) -> dict[str, Any]:
        from datetime import datetime, timedelta

        tier = support_tier.lower()
        sev = severity.lower()
        created = datetime.fromisoformat(ticket_created_at.replace("Z", "+00:00"))

        response_hours = self.RESPONSE_HOURS.get((tier, sev), 8)
        resolution_days = self.RESOLUTION_BUSINESS_DAYS.get((tier, sev), 10)

        response_deadline = created + timedelta(hours=response_hours)
        resolution_deadline = created + timedelta(days=resolution_days)

        return {
            "responseDeadline": response_deadline.isoformat(),
            "resolutionDeadline": resolution_deadline.isoformat(),
            "responseSlaHours": float(response_hours),
            "resolutionSlaBusinessDays": resolution_days,
            "escalationTriggers": [
                "Response SLA breach → Escalate to Support Team Lead",
                "50% resolution SLA elapsed → Escalate to Support Manager",
            ],
            "tierFeatures": self._tier_features(tier),
        }

    def _tier_features(self, tier: str) -> list[str]:
        if tier == "premium":
            return ["24/7 Sev1 support", "Phone support", "Dedicated account manager"]
        return ["Email and portal support", "Business hours only"]


class DateCalculatorService:
    """Business datetime calculations."""

    def calculate(
        self,
        operation: str,
        start: str,
        end: str | None = None,
        hours: float = 0.0,
    ) -> dict[str, Any]:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))

        if operation == "business_hours_remaining":
            if not end:
                raise ValueError("end is required for business_hours_remaining")
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            remaining = max(0.0, (end_dt - start_dt).total_seconds() / 3600.0)
            return {
                "result": remaining,
                "unit": "business_hours",
                "details": f"Hours remaining from {start} to {end}",
            }

        if operation == "add_business_hours":
            from datetime import timedelta

            result_dt = start_dt + timedelta(hours=hours)
            return {
                "result": result_dt.isoformat(),
                "unit": "datetime",
                "details": f"Added {hours} hours to {start}",
            }

        if operation == "diff_business_hours":
            if not end:
                raise ValueError("end is required for diff_business_hours")
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            diff = (end_dt - start_dt).total_seconds() / 3600.0
            return {
                "result": diff,
                "unit": "business_hours",
                "details": f"Difference between {start} and {end}",
            }

        raise ValueError(f"Unknown operation: {operation}")


class DocumentationSearchService:
    """Semantic search over documentation via vector store."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider

    async def search(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> dict[str, Any]:
        embedding = await self._embedding_provider.embed_query(query)
        chunks = await self._vector_store.similarity_search(
            query_embedding=embedding,
            top_k=top_k,
            source_filter=source_filter,
        )
        return {
            "results": [
                {
                    "content": chunk.content,
                    "source_file": chunk.source_file,
                    "section": chunk.section,
                    "score": chunk.score,
                }
                for chunk in chunks
            ]
        }


class ToolRegistry:
    """Shared tool implementations used by MCP server and direct client."""

    def __init__(
        self,
        settings: Settings,
        vector_store: VectorStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._ticket_service = TicketHistoryService(settings.ticket_history_path)
        self._sla_service = SLAPolicyService()
        self._date_service = DateCalculatorService()
        self._doc_search: DocumentationSearchService | None = None
        if vector_store and embedding_provider:
            self._doc_search = DocumentationSearchService(vector_store, embedding_provider)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "lookup_ticket_history":
            return self._ticket_service.lookup(
                customer=str(arguments["customer"]),
                ticket_id=arguments.get("ticket_id"),
                query=arguments.get("query"),
                tags=arguments.get("tags"),
            )
        if tool_name == "check_sla_policy":
            return self._sla_service.check(
                support_tier=str(arguments["support_tier"]),
                severity=str(arguments["severity"]),
                ticket_created_at=str(arguments["ticket_created_at"]),
            )
        if tool_name == "calculate_datetime":
            return self._date_service.calculate(
                operation=str(arguments["operation"]),
                start=str(arguments["start"]),
                end=arguments.get("end"),
                hours=float(arguments.get("hours", 0.0)),
            )
        if tool_name == "search_documentation":
            if not self._doc_search:
                return {"results": [], "error": "Documentation search not configured"}
            return await self._doc_search.search(
                query=str(arguments["query"]),
                top_k=int(arguments.get("top_k", 5)),
                source_filter=arguments.get("source_filter"),
            )
        raise ValueError(f"Unknown tool: {tool_name}")

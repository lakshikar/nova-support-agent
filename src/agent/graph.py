from __future__ import annotations

import logging
import time
from typing import TypedDict

from langgraph.graph import END, StateGraph

from domain.entities.models import (
    EvidenceItem,
    InvestigationPlan,
    InvestigationStep,
    InvestigationTraceEntry,
    ResolutionReport,
    SupportTicket,
    TicketUnderstanding,
    ToolCallRecord,
)
from domain.ports import LLMProvider, MCPToolClient, RequestLogger
from domain.ports.support_agent import utc_now
from domain.value_objects.enums import ConfidenceLevel, Severity, SupportTier, ToolName
from infrastructure.config.settings import Settings


class AgentState(TypedDict):
    request_id: str
    ticket: SupportTicket
    understanding: TicketUnderstanding | None
    plan: InvestigationPlan | None
    evidence: list[EvidenceItem]
    tool_calls: list[ToolCallRecord]
    iteration_count: int
    evidence_sufficient: bool
    report: ResolutionReport | None


class _UnderstandingOutput(TicketUnderstanding):
    pass


class _PlanOutput(InvestigationPlan):
    pass


class _EvaluationOutput(TicketUnderstanding):
    evidence_sufficient: bool = False
    revised_steps: list[InvestigationStep] = []


class _ReportOutput(ResolutionReport):
    pass


SYSTEM_PROMPT = (
    "You are NovaTech's Intelligent Support Agent. Investigate support tickets "
    "using evidence from documentation and ticket history. Be honest about uncertainty."
)

logger = logging.getLogger(__name__)


class LangGraphSupportAgent:
    """LangGraph-based autonomous support investigation agent."""

    def __init__(
        self,
        llm: LLMProvider,
        mcp_client: MCPToolClient,
        settings: Settings,
    ) -> None:
        self._llm = llm
        self._mcp = mcp_client
        self._settings = settings
        self._graph = self._build_graph()

    async def investigate(
        self,
        ticket: SupportTicket,
        request_id: str,
        request_logger: RequestLogger,
    ) -> ResolutionReport:
        initial_state: AgentState = {
            "request_id": request_id,
            "ticket": ticket,
            "understanding": None,
            "plan": None,
            "evidence": [],
            "tool_calls": [],
            "iteration_count": 0,
            "evidence_sufficient": False,
            "report": None,
        }
        self._logger = request_logger
        logger.info(
            "[%s] Graph started customer=%s tier=%s subject=%r",
            request_id,
            ticket.customer,
            ticket.support_tier.value,
            ticket.subject,
        )
        result = await self._graph.ainvoke(initial_state)
        report = result.get("report")
        if not report:
            raise RuntimeError("Agent failed to produce a resolution report")
        logger.info(
            "[%s] Graph finished confidence=%s diagnosis=%r",
            request_id,
            report.confidence_level.value,
            report.diagnosis[:120],
        )
        return report

    def _build_graph(self) -> object:
        graph = StateGraph(AgentState)
        graph.add_node("understand_ticket", self._understand_ticket)
        graph.add_node("plan_investigation", self._plan_investigation)
        graph.add_node("execute_next_step", self._execute_next_step)
        graph.add_node("evaluate_evidence", self._evaluate_evidence)
        graph.add_node("synthesize_report", self._synthesize_report)

        graph.set_entry_point("understand_ticket")
        graph.add_edge("understand_ticket", "plan_investigation")
        graph.add_edge("plan_investigation", "execute_next_step")
        graph.add_edge("execute_next_step", "evaluate_evidence")
        graph.add_conditional_edges(
            "evaluate_evidence",
            self._should_continue,
            {"continue": "execute_next_step", "finish": "synthesize_report"},
        )
        graph.add_edge("synthesize_report", END)
        return graph.compile()

    def _should_continue(self, state: AgentState) -> str:
        if state["evidence_sufficient"]:
            decision = "finish"
        elif state["iteration_count"] >= self._settings.max_agent_iterations:
            decision = "finish"
        elif state.get("plan") and any(not step.completed for step in state["plan"].steps):
            decision = "continue"
        else:
            decision = "finish"
        logger.info(
            "[%s] Route evaluate_evidence -> %s (sufficient=%s iterations=%s pending_steps=%s)",
            state["request_id"],
            decision,
            state["evidence_sufficient"],
            state["iteration_count"],
            sum(1 for s in (state.get("plan").steps if state.get("plan") else []) if not s.completed),
        )
        return decision

    async def _understand_ticket(self, state: AgentState) -> dict[str, object]:
        start = time.perf_counter()
        request_id = state["request_id"]
        ticket = state["ticket"]
        logger.info("[%s] Node understand_ticket: extracting ticket context", request_id)
        prompt = f"""Analyze this support ticket and extract structured information.

Subject: {ticket.subject}
Body: {ticket.body}
Customer: {ticket.customer}
Support Tier: {ticket.support_tier.value}
Ticket References: {ticket.ticket_references}

Extract: affected module, error codes (NT-XXXX format), severity, urgency rationale,
referenced ticket IDs (TK-XXXXX format), keywords, and whether the issue is ambiguous.
Note: references like #NT-4523 may be error codes, not ticket IDs.
Use severity one of: critical, high, medium, low.
Use support_tier one of: standard, premium."""

        understanding = await self._llm.invoke_structured(
            prompt,
            TicketUnderstanding,
            system=SYSTEM_PROMPT,
        )
        understanding.support_tier = ticket.support_tier

        duration = int((time.perf_counter() - start) * 1000)
        logger.info(
            "[%s] Node understand_ticket: module=%s errors=%s severity=%s ambiguous=%s (%dms)",
            request_id,
            understanding.affected_module,
            understanding.error_codes,
            understanding.severity.value,
            understanding.is_ambiguous,
            duration,
        )
        self._logger.log_decision(
            request_id,
            "understand_ticket",
            ticket.subject,
            f"module={understanding.affected_module}, errors={understanding.error_codes}",
            duration,
        )
        return {"understanding": understanding}

    async def _plan_investigation(self, state: AgentState) -> dict[str, object]:
        start = time.perf_counter()
        request_id = state["request_id"]
        ticket = state["ticket"]
        understanding = state["understanding"]
        assert understanding is not None
        logger.info("[%s] Node plan_investigation: building tool plan", request_id)
        prompt = f"""Create an investigation plan for this ticket. Choose tools and order based on
the ticket specifics — do NOT use a fixed sequence.

Available tools:
- search_documentation (params: query, top_k)
- lookup_ticket_history (params: customer, ticket_id, query, tags)
- check_sla_policy (params: support_tier, severity, ticket_created_at)
- calculate_datetime (params: operation, start, end, hours)

Ticket:
Subject: {ticket.subject}
Body: {ticket.body}
Understanding: {understanding.model_dump_json()}

Return an InvestigationPlan with ordered steps and strategy_summary."""

        plan = await self._llm.invoke_structured(
            prompt,
            InvestigationPlan,
            system=SYSTEM_PROMPT,
        )
        plan = self._apply_guardrails(plan, understanding, ticket)

        duration = int((time.perf_counter() - start) * 1000)
        step_summary = ", ".join(f"{s.tool}" for s in plan.steps)
        logger.info(
            "[%s] Node plan_investigation: %d steps [%s] (%dms)",
            request_id,
            len(plan.steps),
            step_summary,
            duration,
        )
        self._logger.log_decision(
            request_id,
            "plan_investigation",
            understanding.model_dump_json(),
            plan.strategy_summary,
            duration,
        )
        return {"plan": plan, "iteration_count": 0}

    def _apply_guardrails(
        self,
        plan: InvestigationPlan,
        understanding: TicketUnderstanding,
        ticket: SupportTicket,
    ) -> InvestigationPlan:
        tools_present = {step.tool for step in plan.steps}

        if understanding.error_codes and ToolName.SEARCH_DOCUMENTATION.value not in tools_present:
            logger.info("Guardrail: inserting search_documentation for error codes")
            plan.steps.insert(
                0,
                InvestigationStep(
                    tool=ToolName.SEARCH_DOCUMENTATION.value,
                    rationale="Guardrail: error code detected",
                    parameters={"query": " ".join(understanding.error_codes)},
                ),
            )

        if ToolName.CHECK_SLA_POLICY.value not in tools_present:
            logger.info("Guardrail: inserting check_sla_policy")
            created = (ticket.created_at or utc_now()).isoformat()
            plan.steps.append(
                InvestigationStep(
                    tool=ToolName.CHECK_SLA_POLICY.value,
                    rationale="Guardrail: SLA check required",
                    parameters={
                        "support_tier": ticket.support_tier.value,
                        "severity": understanding.severity.value,
                        "ticket_created_at": created,
                    },
                )
            )

        return plan

    async def _execute_next_step(self, state: AgentState) -> dict[str, object]:
        request_id = state["request_id"]
        plan = state.get("plan")
        if not plan:
            return {"iteration_count": state["iteration_count"] + 1}

        pending_steps = [step for step in plan.steps if not step.completed]
        if not pending_steps:
            return {"iteration_count": state["iteration_count"] + 1}

        logger.info(
            "[%s] Node execute_next_step: running %d tool(s)",
            request_id,
            len(pending_steps),
        )
        ticket = state["ticket"]
        evidence = list(state["evidence"])
        tool_calls = list(state["tool_calls"])
        iteration_count = state["iteration_count"]

        for next_step in pending_steps:
            params = dict(next_step.parameters)
            if next_step.tool == ToolName.LOOKUP_TICKET_HISTORY.value:
                params.setdefault("customer", ticket.customer)

            start = time.perf_counter()
            logger.info(
                "[%s] Tool call %s params=%s",
                request_id,
                next_step.tool,
                params,
            )
            try:
                result = await self._mcp.call_tool(next_step.tool, params)
                success = True
            except Exception as exc:
                result = {"error": str(exc)}
                success = False

            next_step.completed = True
            evidence.append(
                EvidenceItem(
                    tool=next_step.tool,
                    query_summary=next_step.rationale,
                    result=result,
                    source_refs=self._extract_source_refs(result),
                )
            )
            tool_calls.append(
                ToolCallRecord(
                    tool=next_step.tool,
                    parameters=params,
                    result_summary=str(result)[:500],
                    timestamp=utc_now(),
                    success=success,
                )
            )

            duration = int((time.perf_counter() - start) * 1000)
            logger.info(
                "[%s] Tool result %s success=%s (%dms) refs=%s",
                request_id,
                next_step.tool,
                success,
                duration,
                self._extract_source_refs(result),
            )
            self._logger.log_tool_call(
                request_id,
                next_step.tool,
                params,
                result,
                success,
            )
            self._logger.log_decision(
                request_id,
                "execute_next_step",
                next_step.rationale,
                f"tool={next_step.tool}, success={success}",
                duration,
            )
            iteration_count += 1

        return {
            "plan": plan,
            "evidence": evidence,
            "tool_calls": tool_calls,
            "iteration_count": iteration_count,
        }

    async def _evaluate_evidence(self, state: AgentState) -> dict[str, object]:
        start = time.perf_counter()
        request_id = state["request_id"]
        evidence = state["evidence"]
        plan = state.get("plan")
        pending_steps = [step for step in (plan.steps if plan else []) if not step.completed]

        sufficient = bool(evidence) and not pending_steps
        if not evidence:
            sufficient = False
        if state["iteration_count"] >= self._settings.max_agent_iterations:
            sufficient = True

        duration = int((time.perf_counter() - start) * 1000)
        logger.info(
            "[%s] Node evaluate_evidence: sufficient=%s evidence=%d pending=%d (%dms)",
            request_id,
            sufficient,
            len(evidence),
            len(pending_steps),
            duration,
        )
        self._logger.log_decision(
            request_id,
            "evaluate_evidence",
            f"{len(evidence)} evidence items",
            f"sufficient={sufficient}, pending_steps={len(pending_steps)}",
            duration,
        )
        return {"evidence_sufficient": sufficient}

    async def _synthesize_report(self, state: AgentState) -> dict[str, object]:
        start = time.perf_counter()
        request_id = state["request_id"]
        ticket = state["ticket"]
        understanding = state["understanding"]
        evidence = state["evidence"]
        logger.info(
            "[%s] Node synthesize_report: generating resolution from %d evidence item(s)",
            request_id,
            len(evidence),
        )

        prompt = f"""Synthesize a structured resolution report from the investigation evidence.

Ticket:
Subject: {ticket.subject}
Body: {ticket.body}
Customer: {ticket.customer}
Support Tier: {ticket.support_tier.value}

Understanding: {understanding.model_dump_json() if understanding else '{}'}
Evidence: {[e.model_dump() for e in evidence]}

Produce a complete ResolutionReport with:
- diagnosis
- recommended_resolution (step-by-step list)
- confidence_level (high/medium/low) and confidence_rationale
- sla_status if SLA evidence exists
- sources (documents, tickets, known issues cited)
- escalation_recommendation
- investigation_gaps (empty if confident)
- investigation_trace entries for each major step

Set request_id to "{request_id}".
Be honest about uncertainty for ambiguous tickets.
Use confidence_level one of: high, medium, low.
investigation_trace may be an empty list."""

        report = await self._llm.invoke_structured(
            prompt,
            ResolutionReport,
            system=SYSTEM_PROMPT,
        )
        report.request_id = state["request_id"]

        if not report.investigation_trace:
            report.investigation_trace = [
                InvestigationTraceEntry(
                    step=call.tool,
                    action=call.result_summary[:200],
                    result="completed" if call.success else "failed",
                    timestamp=call.timestamp,
                )
                for call in state["tool_calls"]
            ]

        duration = int((time.perf_counter() - start) * 1000)
        logger.info(
            "[%s] Node synthesize_report: confidence=%s (%dms)",
            request_id,
            report.confidence_level.value,
            duration,
        )
        self._logger.log_decision(
            request_id,
            "synthesize_report",
            f"{len(evidence)} evidence items",
            f"confidence={report.confidence_level.value}",
            duration,
        )
        return {"report": report}

    def _extract_source_refs(self, result: dict[str, object]) -> list[str]:
        refs: list[str] = []
        if "results" in result and isinstance(result["results"], list):
            for item in result["results"]:
                if isinstance(item, dict):
                    source = item.get("source_file") or item.get("content", "")[:50]
                    refs.append(str(source))
        if "tickets" in result and isinstance(result["tickets"], list):
            for ticket in result["tickets"]:
                if isinstance(ticket, dict) and ticket.get("ticketId"):
                    refs.append(str(ticket["ticketId"]))
        return refs

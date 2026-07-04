from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domain.value_objects.enums import ConfidenceLevel, Severity, SourceType, SupportTier


class SupportTicket(BaseModel):
    subject: str
    body: str
    customer: str
    support_tier: SupportTier = Field(alias="supportTier")
    created_at: datetime | None = Field(default=None, alias="createdAt")
    ticket_references: list[str] = Field(default_factory=list, alias="ticketReferences")

    model_config = {"populate_by_name": True}


class TicketUnderstanding(BaseModel):
    affected_module: str | None = None
    error_codes: list[str] = Field(default_factory=list)
    support_tier: SupportTier
    severity: Severity
    urgency_rationale: str = ""
    referenced_ticket_ids: list[str] = Field(default_factory=list)
    referenced_error_codes: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    is_ambiguous: bool = False


class InvestigationStep(BaseModel):
    tool: str
    rationale: str
    parameters: dict[str, object] = Field(default_factory=dict)
    completed: bool = False


class InvestigationPlan(BaseModel):
    steps: list[InvestigationStep] = Field(default_factory=list)
    strategy_summary: str = ""


class EvidenceItem(BaseModel):
    tool: str
    query_summary: str
    result: dict[str, object]
    source_refs: list[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    tool: str
    parameters: dict[str, object]
    result_summary: str
    timestamp: datetime
    success: bool = True


class SourceReference(BaseModel):
    type: SourceType
    id: str
    title: str
    relevance: str = ""


class SLAStatus(BaseModel):
    support_tier: SupportTier
    severity: Severity
    response_deadline: datetime
    resolution_deadline: datetime
    response_remaining_business_hours: float
    resolution_remaining_business_hours: float
    escalation_required: bool = False
    escalation_reason: str | None = None


class EscalationRecommendation(BaseModel):
    required: bool
    reason: str
    suggested_level: str = "support_engineer"


class InvestigationTraceEntry(BaseModel):
    step: str
    action: str
    result: str
    timestamp: datetime


class ResolutionReport(BaseModel):
    request_id: str
    diagnosis: str
    recommended_resolution: list[str]
    confidence_level: ConfidenceLevel
    confidence_rationale: str
    sla_status: SLAStatus | None = None
    sources: list[SourceReference] = Field(default_factory=list)
    escalation_recommendation: EscalationRecommendation
    investigation_gaps: list[str] = Field(default_factory=list)
    investigation_trace: list[InvestigationTraceEntry] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    content: str
    source_file: str
    section: str
    score: float = 0.0
    metadata: dict[str, object] = Field(default_factory=dict)

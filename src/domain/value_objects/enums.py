from __future__ import annotations

from enum import Enum


class SupportTier(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceType(str, Enum):
    DOCUMENT = "document"
    TICKET = "ticket"
    KNOWN_ISSUE = "known_issue"


class ToolName(str, Enum):
    SEARCH_DOCUMENTATION = "search_documentation"
    LOOKUP_TICKET_HISTORY = "lookup_ticket_history"
    CHECK_SLA_POLICY = "check_sla_policy"
    CALCULATE_DATETIME = "calculate_datetime"

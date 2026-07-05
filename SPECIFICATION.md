# SPECIFICATION.md — NovaTech Intelligent Support Agent

System design blueprints for the proof-of-concept Intelligent Support Agent.

## 1. Problem Statement

NovaTech Industries handles ~500 support tickets/day. Support engineers manually investigate
each ticket — reading issues, searching docs, checking history, classifying severity, and
drafting resolutions. This PoC builds an autonomous agent that investigates tickets and
produces structured resolution reports.

## 2. Non-Goals

- Production-ready polished UI
- Multi-tenant SaaS deployment
- Real-time ticket system integration
- Authentication/authorization beyond customer-scoped ticket lookup

## 3. Agent Contract — Five Steps

| Step | Name | Responsibility |
|---|---|---|
| 1 | Understand Ticket | Extract module, error codes, tier, urgency, references |
| 2 | Plan Investigation | Generate ticket-specific investigation steps (not fixed pipeline) |
| 3 | Investigate | Execute MCP tools/skills to gather evidence |
| 4 | Reason Across Evidence | Combine sources; handle gaps and conflicts honestly |
| 5 | Produce Report | Structured JSON resolution report |

## 4. API Contract

### 4.1 Input — Support Ticket

`POST /api/v1/investigate`

```json
{
  "subject": "string (required)",
  "body": "string (required)",
  "customer": "string (required)",
  "supportTier": "standard | premium (required)",
  "createdAt": "ISO-8601 datetime (optional, defaults to now)",
  "ticketReferences": ["TK-20251"]
}
```

### 4.2 Output — Resolution Report

```json
{
  "requestId": "uuid",
  "diagnosis": "string",
  "recommendedResolution": ["step 1", "step 2"],
  "confidenceLevel": "high | medium | low",
  "confidenceRationale": "string",
  "slaStatus": {
    "supportTier": "standard | premium",
    "severity": "critical | high | medium | low",
    "responseDeadline": "ISO-8601",
    "resolutionDeadline": "ISO-8601",
    "responseRemainingBusinessHours": 0.0,
    "resolutionRemainingBusinessHours": 0.0,
    "escalationRequired": false,
    "escalationReason": "string | null"
  },
  "sources": [
    {
      "type": "document | ticket | known_issue",
      "id": "string",
      "title": "string",
      "relevance": "string"
    }
  ],
  "escalationRecommendation": {
    "required": false,
    "reason": "string",
    "suggestedLevel": "support_engineer | senior_engineer | support_manager"
  },
  "investigationGaps": ["string"],
  "investigationTrace": [
    {
      "step": "string",
      "action": "string",
      "result": "string",
      "timestamp": "ISO-8601"
    }
  ]
}
```

## 5. LangGraph Agent

### 5.1 State Schema (`AgentState`)

| Field | Type | Description |
|---|---|---|
| `request_id` | str | UUID for logging |
| `ticket` | SupportTicket | Input ticket |
| `understanding` | TicketUnderstanding | Extracted entities |
| `plan` | InvestigationPlan | Ordered investigation steps |
| `evidence` | list[EvidenceItem] | Collected tool results |
| `tool_calls` | list[ToolCallRecord] | Audit trail of MCP calls |
| `iteration_count` | int | Loop counter (max 8) |
| `evidence_sufficient` | bool | Evaluation result |
| `report` | ResolutionReport | Final output |

### 5.2 Nodes

| Node | Input | Output | LLM? |
|---|---|---|---|
| `understand_ticket` | ticket | understanding | Yes (structured) |
| `plan_investigation` | ticket, understanding | plan | Yes (structured) |
| `execute_next_step` | plan, evidence | evidence+, tool_calls+ | No |
| `evaluate_evidence` | evidence, plan | evidence_sufficient, plan (revised) | Yes |
| `synthesize_report` | all evidence | report | Yes (structured) |

### 5.3 Graph Edges

```
START → understand_ticket → plan_investigation → execute_next_step
  → evaluate_evidence → [conditional]
    if not sufficient AND iteration < 8 → execute_next_step
    else → synthesize_report → END
```

### 5.4 Guardrails (non-LLM)

- If error code detected in understanding → ensure `search_documentation` is in plan
- If support tier known → ensure `check_sla_policy` is in plan
- Max 8 investigation iterations

## 6. MCP Tool Contracts

All tools exposed by the MCP server container.

### 6.1 `search_documentation`

Semantic search over NovaTech documentation in pgvector.

**Parameters:**
```json
{
  "query": "string (required)",
  "top_k": 5,
  "source_filter": "string | null"
}
```

**Returns:**
```json
{
  "results": [
    {
      "content": "string",
      "source_file": "string",
      "section": "string",
      "score": 0.95
    }
  ]
}
```

### 6.2 `lookup_ticket_history`

Search past tickets with **mandatory customer scope**.

**Parameters:**
```json
{
  "customer": "string (required)",
  "ticket_id": "string | null",
  "query": "string | null",
  "tags": ["string"]
}
```

**Returns:**
```json
{
  "tickets": [
    {
      "ticketId": "string",
      "subject": "string",
      "status": "string",
      "resolution": "string | null",
      "tags": ["string"]
    }
  ]
}
```

**Isolation rule:** If `ticket_id` belongs to a different customer, return empty list
and log access denial. Never return cross-customer data.

### 6.3 `check_sla_policy`

Determine SLA deadlines and escalation rules.

**Parameters:**
```json
{
  "support_tier": "standard | premium",
  "severity": "critical | high | medium | low",
  "ticket_created_at": "ISO-8601"
}
```

**Returns:**
```json
{
  "responseDeadline": "ISO-8601",
  "resolutionDeadline": "ISO-8601",
  "responseSlaHours": 4.0,
  "resolutionSlaBusinessDays": 5,
  "escalationTriggers": ["string"],
  "tierFeatures": ["string"]
}
```

### 6.4 `calculate_datetime`

Business-day and datetime calculations.

**Parameters:**
```json
{
  "operation": "business_hours_remaining | add_business_hours | diff_business_hours",
  "start": "ISO-8601",
  "end": "ISO-8601 | null",
  "hours": 0.0
}
```

**Returns:**
```json
{
  "result": 0.0,
  "unit": "business_hours | datetime",
  "details": "string"
}
```

## 7. Tools vs Skills

| Category | Examples | Where Implemented |
|---|---|---|
| **Tools** | ticket lookup, SLA check, date calc | MCP server (deterministic) |
| **Skills** | doc search & retrieval, synthesis | MCP `search_documentation` + LangGraph synthesis node |

Skills involve retrieval, relevance judgment, and multi-source reasoning.
Tools are single-purpose, deterministic lookups.

## 8. LLM Provider Interface

### Port: `LLMProvider`

```python
async def invoke_structured(
    self, prompt: str, schema: type[BaseModel], system: str | None = None
) -> BaseModel: ...

async def invoke(self, prompt: str, system: str | None = None) -> str: ...
```

### Configuration (environment variables)

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `nvidia`, `groq`, `openai`, `ollama` | `nvidia` |
| `NVIDIA_API_KEY` | NVIDIA NIM API key | — |
| `NVIDIA_BASE_URL` | NVIDIA API base URL | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_MODEL` | NVIDIA chat model | `meta/llama-3.3-70b-instruct` |
| `GROQ_API_KEY` | Groq API key | — |
| `GROQ_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama3` |
| `EMBEDDING_PROVIDER` | `nvidia`, `openai`, `ollama` | `nvidia` |
| `NVIDIA_EMBEDDING_MODEL` | NVIDIA embedding model | `nvidia/nv-embed-v1` |
| `EMBEDDING_DIMENSIONS` | Vector dimensions for pgvector | `4096` |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` |

## 9. Vector Store

- **Engine:** PostgreSQL 16 with pgvector extension
- **Table:** `document_chunks(id, content, embedding, source_file, section, metadata)`
- **Chunking:** Markdown-aware split on `##` headers; max ~500 tokens per chunk
- **Ingestion:** Manual via `scripts/ingest_documents.py`; auto on compose startup if table empty

## 10. Observability — Request Decision Log

Each `POST /api/v1/investigate` creates `logs/{request_id}.json`:

```json
{
  "requestId": "uuid",
  "startedAt": "ISO-8601",
  "completedAt": "ISO-8601",
  "elapsedMs": 1234,
  "input": { },
  "decisions": [
    {
      "node": "understand_ticket",
      "timestamp": "ISO-8601",
      "inputSummary": "string",
      "outputSummary": "string",
      "durationMs": 100
    }
  ],
  "toolCalls": [ ],
  "output": { }
}
```

## 11. Tenant Isolation

- Ticket history lookups require `customer` parameter
- Cross-customer ticket ID lookups return empty results
- Unit and integration tests must assert isolation

## 12. Example Ticket Success Criteria

| Ticket | Key Expectations |
|---|---|
| 1 (NT-4523) | Find KI-2402-001, legacy endpoint workaround, high confidence |
| 2 (Atlas multi-ticket) | Lookup TK-20251, SLA for Standard, related-but-distinct reasoning |
| 3 (ambiguous slowness) | Broad search, KI-2402-006, low confidence, escalation recommended |

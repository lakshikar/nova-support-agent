# NovaTech Intelligent Support Agent — Architecture

## Overview

The Intelligent Support Agent autonomously investigates customer support tickets and
produces structured resolution reports. It is a proof-of-concept, not a production system.

## High-Level Architecture

See [`architecture.drawio`](architecture.drawio) for an editable diagram.

```
Client → REST API → InvestigateTicketUseCase → LangGraph Agent
                                                    ↓
                              LLM Provider (Groq/OpenAI/Ollama)
                                                    ↓
                              MCP Tool Client → Tool Registry
                                                    ↓
                         ┌──────────┬──────────────┬──────────────┐
                         │ pgvector │ ticket JSON  │ SLA policy   │
                         └──────────┴──────────────┴──────────────┘
```

## Agent Reasoning Flow

The agent does **not** follow a fixed pipeline. Each ticket triggers a different plan:

1. **Understand** — LLM extracts module, error codes, severity, references
2. **Plan** — LLM generates ticket-specific investigation steps
3. **Execute** — MCP tools gather evidence (loop)
4. **Evaluate** — LLM decides if evidence is sufficient
5. **Synthesize** — Structured resolution report with confidence and gaps

Guardrails (non-LLM) ensure error codes trigger doc search and tier triggers SLA check.

## Framework Choices

### LangGraph

Chosen over a fixed LangChain chain because:
- Support tickets require **cyclical reasoning** (investigate → evaluate → investigate more)
- Conditional routing based on evidence sufficiency
- Explicit state schema for observability and debugging

A simple chain would hardcode tool order; LangGraph lets the agent revise its plan.

### LangChain

Used for:
- LLM provider adapters (Groq, OpenAI, Ollama)
- Embedding models for document ingestion
- Structured output parsing

Not used for the main orchestration loop.

### MCP (Model Context Protocol)

Tools run in a separate MCP server container:
- **Isolation** — tool failures don't crash the agent
- **Testability** — tools tested independently; agent tests mock `MCPToolClient`
- **Docker alignment** — matches the required compose architecture

The API container uses `DirectMCPToolClient` (in-process) sharing the same `ToolRegistry`
as the MCP server for simpler local dev. Both paths call identical tool logic.

### PostgreSQL + pgvector

Chosen over in-memory FAISS because:
- Persistent document store across restarts
- Production-like retrieval for the PoC
- Docker-compose requirement

Trade-off: requires PostgreSQL setup; unit tests use `InMemoryVectorStore`.

## Tools vs Skills

| Type | Definition | Examples |
|---|---|---|
| **Tool** | Single deterministic MCP call | `check_sla_policy`, `calculate_datetime` |
| **Skill** | Multi-step capability with judgment | Doc search (embed → retrieve → rank); synthesis (combine sources → report) |

Skills live at the orchestration layer (LangGraph nodes) or combine multiple operations.
Tools are atomic MCP endpoints.

## Key Design Decisions

| Decision | Chosen | Alternatives Considered | Rationale |
|---|---|---|---|
| Default LLM | NVIDIA NIM (Llama 3.3 70B) | Groq, OpenAI, Ollama | Free tier API; OpenAI-compatible |
| Embeddings | NVIDIA nv-embed-v1 (4096d) | OpenAI, Ollama | High-quality retrieval; requires dimension config |
| Agent pattern | Plan-Execute-Evaluate loop | ReAct only, fixed pipeline | Shows autonomous planning per ticket |
| Tool transport | Shared ToolRegistry + MCP wrapper | Tools only in agent | Clean Architecture + MCP requirement |
| Max iterations | 8 | Unlimited | Prevents runaway agent loops |
| Confidence | Explicit in report | Hidden | Honest uncertainty for ambiguous tickets |
| Logging | JSON file per request | Structured logging only | Required observability artifact |

## Observability

Every `POST /api/v1/investigate` creates `logs/{request_id}.json` containing:
- Input ticket
- Each agent node decision (understand, plan, execute, evaluate, synthesize)
- All MCP tool calls with parameters and results
- Final report and elapsed time

## Clean Architecture Layers

- **Domain** — `SupportTicket`, `ResolutionReport`, port interfaces
- **Use Cases** — `InvestigateTicketUseCase`, `IngestDocumentsUseCase`
- **Infrastructure** — Groq/OpenAI/Ollama adapters, pgvector, file logger
- **Agent** — LangGraph graph (orchestration)
- **API** — FastAPI HTTP layer with dependency injection

Dependency Inversion: the agent depends on `LLMProvider` and `MCPToolClient` ports,
not on Groq or PostgreSQL directly.

## Tenant Isolation

Ticket history lookups require a `customer` parameter. Cross-customer ticket ID
lookups return empty results with `access_denied: true`. Tests in
`tests/unit/test_mcp_tools.py` and `tests/integration/test_ticket_validation.py`
verify this behavior.

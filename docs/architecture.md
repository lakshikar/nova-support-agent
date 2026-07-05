# NovaTech Intelligent Support Agent — Architecture

## Overview

The Intelligent Support Agent autonomously investigates customer support tickets and
produces structured resolution reports. It is a proof-of-concept, not a production system.

## Architecture Diagrams


| View       | File                                                         | Description                                             |
| ---------- | ------------------------------------------------------------ | ------------------------------------------------------- |
| High-Level | `[architecture.drawio](architecture.drawio)`                 | End-to-end data flow from client to tools               |
| Logical    | `[logical-view.drawio](logical-view.drawio)`                 | Clean Architecture layers, ports, and adapters          |
| Deployment | `[deployment-view.drawio](deployment-view.drawio)`           | Docker Compose services, volumes, and external APIs     |
| Agent Flow | `[agent-reasoning-flow.drawio](agent-reasoning-flow.drawio)` | LangGraph nodes, guardrails, and evaluate/continue loop |


Open any `.drawio` file in [draw.io](https://app.diagrams.net/) or the VS Code Draw.io extension.

## High-Level Architecture

See `[architecture.drawio](architecture.drawio)` for an editable diagram.

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


| Type      | Definition                          | Examples                                                                   |
| --------- | ----------------------------------- | -------------------------------------------------------------------------- |
| **Tool**  | Single deterministic MCP call       | `check_sla_policy`, `calculate_datetime`                                   |
| **Skill** | Multi-step capability with judgment | Doc search (embed → retrieve → rank); synthesis (combine sources → report) |


Skills live at the orchestration layer (LangGraph nodes) or combine multiple operations.
Tools are atomic MCP endpoints.

## Key Design Decisions


| Decision       | Chosen                            | Alternatives Considered    | Rationale                                         |
| -------------- | --------------------------------- | -------------------------- | ------------------------------------------------- |
| Default LLM    | NVIDIA NIM (Llama 3.3 70B)        | Groq, OpenAI, Ollama       | Free tier API; OpenAI-compatible                  |
| Embeddings     | NVIDIA nv-embed-v1 (4096d)        | OpenAI, Ollama             | High-quality retrieval; requires dimension config |
| Agent pattern  | Plan-Execute-Evaluate loop        | ReAct only, fixed pipeline | Shows autonomous planning per ticket              |
| Tool transport | Shared ToolRegistry + MCP wrapper | Tools only in agent        | Clean Architecture + MCP requirement              |
| Max iterations | 8                                 | Unlimited                  | Prevents runaway agent loops                      |
| Confidence     | Explicit in report                | Hidden                     | Honest uncertainty for ambiguous tickets          |
| Logging        | JSON file per request             | Structured logging only    | Required observability artifact                   |




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

## Future Improvements

Highest-impact enhancements for a follow-on iteration (if given more time): 


| #   | Area  | Improvement                                                        | Why it matters                                                                                                                              |
| --- | ----- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Agent | LLM-based `evaluate_evidence` with plan revision (`revised_steps`) | Today evaluation only checks whether all plan steps are done; it does not judge evidence quality, resolve conflicts, or add follow-up steps |
| 2   | Agent | Run one tool per loop in `execute_next_step`                       | Executing all pending tools in one visit weakens the plan → evaluate cycle and makes iteration limits less predictable                      |
| 3   | RAG   | Token-based chunking, overlap, and idempotent re-ingest            | Improves retrieval boundaries; `force=True` ingest should not duplicate chunks; aligns chunk size with the ~500-token spec                  |
| 4   | RAG   | Hybrid search (BM25 + vector) with optional reranking              | Pure cosine similarity can miss exact error codes (e.g. `NT-4523`) and other keyword-strong matches                                         |



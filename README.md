# NovaTech Intelligent Support Agent

Proof-of-concept autonomous support agent for NovaTech Industries. Given a raw
support ticket, the agent understands the issue, plans an investigation,
gathers evidence via MCP tools, and produces a structured resolution report.

## Architecture

- **LangGraph** — dynamic agent orchestration with plan → investigate → evaluate loop
- **LangChain** — LLM adapters, embeddings, document loaders
- **MCP** — isolated tool server (documentation search, ticket history, SLA, datetime)
- **PostgreSQL + pgvector** — semantic documentation retrieval
- **FastAPI** — REST API (`POST /api/v1/investigate`)
- **Clean Architecture** — domain ports with infrastructure adapters (see `AGENTS.md`)

See [`docs/architecture.md`](docs/architecture.md) for design decisions and diagrams.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- NVIDIA NIM API key (default LLM and embeddings) or Groq/OpenAI/Ollama

## Quick Start (Docker)

1. Copy environment file and set your API key:

```bash
cp .env.example .env
# Edit .env — set NVIDIA_API_KEY (default LLM and embeddings)
```

2. Start all services:

```bash
docker compose up --build
```

3. Investigate Ticket 1:

```bash
curl -X POST http://localhost:8000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Error NT-4523 when generating asset report",
    "body": "We are getting error NT-4523 every time we try to generate the quarterly asset depreciation report in the Asset Lifecycle module. This started after upgrading to v24.2.",
    "customer": "Meridian Energy",
    "supportTier": "premium"
  }'
```

4. Check the decision log:

```bash
ls logs/
cat logs/<request-id>.json
```

## Local Development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start PostgreSQL with pgvector separately, then:
python scripts/ingest_documents.py
uvicorn api.main:app --app-dir src --reload
```

## Switch LLM Provider

Set in `.env`:

```bash
LLM_PROVIDER=nvidia   # default
LLM_PROVIDER=groq
LLM_PROVIDER=openai
LLM_PROVIDER=ollama

EMBEDDING_PROVIDER=nvidia   # default
EMBEDDING_PROVIDER=openai   # set EMBEDDING_DIMENSIONS=1536 and re-ingest
EMBEDDING_PROVIDER=ollama
```

> **Note:** Switching embedding providers changes vector dimensions. Set `EMBEDDING_DIMENSIONS`
> accordingly (4096 for NVIDIA, 1536 for OpenAI) and re-ingest docs with `POST /api/v1/ingest?force=true`.

## Run Tests

```bash
pip install -r requirements.txt
pytest
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/investigate` | Investigate a support ticket |
| POST | `/api/v1/ingest` | Ingest/re-ingest documentation |

## Project Structure

```
src/domain/          Entities, value objects, port interfaces
src/use_cases/       Application logic
src/infrastructure/  LLM, pgvector, MCP client, logging adapters
src/agent/           LangGraph agent graph and nodes
src/api/             FastAPI REST layer
mcp_server/          MCP tool server (Docker container)
data/                Mock documentation and ticket history
logs/                Per-request agent decision logs
docs/                Architecture documentation
```

## Spec-Driven Development

- [`AGENTS.md`](AGENTS.md) — coding standards and layer rules
- [`SPECIFICATION.md`](SPECIFICATION.md) — system design blueprints

## Example Tickets

Three test tickets are defined in `tests/integration/test_ticket_validation.py`:

1. **Ticket 1** — NT-4523 depreciation report error (straightforward)
2. **Ticket 2** — Atlas Manufacturing multi-ticket SLA prioritization
3. **Ticket 3** — TerraCore Utilities ambiguous system slowness

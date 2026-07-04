# AGENTS.md — NovaTech Intelligent Support Agent

Guidance for AI agents and engineers working on this codebase.

## Language & Tooling

- **Python 3.11+** required
- **Strict PEP 8** compliance; line length 100 characters
- **Ruff** for formatting and linting (`ruff check`, `ruff format`)
- **Explicit type hints** on all public functions, methods, and class attributes
- Use `from __future__ import annotations` in modules with forward references

## Architecture — Clean Architecture Layers

```
src/
├── domain/          # Entities, value objects, port interfaces (no external deps)
├── use_cases/       # Application business rules; depends on domain only
├── infrastructure/  # Adapters: LLM, DB, MCP, logging (implements domain ports)
├── agent/           # LangGraph orchestration (depends on domain + use_cases)
└── api/             # FastAPI HTTP layer (depends on use_cases + domain)
```

### Dependency Rule

| Layer | May Import From |
|---|---|
| `domain` | Standard library, typing, pydantic (models only) |
| `use_cases` | `domain` |
| `infrastructure` | `domain`, third-party libs |
| `agent` | `domain`, `use_cases`, LangGraph/LangChain |
| `api` | `domain`, `use_cases`, FastAPI |

**Never** import infrastructure adapters (Groq, psycopg, MCP SDK) from `domain` or `use_cases`.

## SOLID Principles

### Single Responsibility (S)
Each LangGraph node performs one task. Each MCP tool exposes one capability.

### Open/Closed (O)
Add new LLM providers by creating a new adapter class implementing `LLMProvider`.
Do not modify the agent graph when adding providers.

### Liskov Substitution (L)
All `LLMProvider` implementations must be interchangeable via the factory.

### Interface Segregation (I)
Ports are small and focused: `LLMProvider`, `VectorStore`, `MCPToolClient`, `RequestLogger`.

### Dependency Inversion (D)
High-level modules depend on abstractions (ports), not concretions:

```python
# Good — use case receives port
class InvestigateTicketUseCase:
    def __init__(self, agent: SupportAgent, logger: RequestLogger) -> None: ...

# Bad — use case imports Groq directly
from langchain_groq import ChatGroq
```

## Naming Conventions

- **Modules:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/methods:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Port interfaces:** noun or `*Provider`, `*Client`, `*Repository`
- **Adapters:** `{Technology}{PortName}` e.g. `GroqLLMProvider`, `PgVectorStore`

## Testing Standards

- **pytest** for all tests; place in `tests/unit/` and `tests/integration/`
- Mock all external dependencies (LLM APIs, MCP server, PostgreSQL) in unit tests
- **Tenant isolation:** tests must verify that ticket lookups scoped to Customer A
  cannot return Customer B's tickets
- One test file per module under test
- Use fixtures in `tests/conftest.py` for shared mocks

## Incremental Build-Test-Learn Loop

For every architectural component:

1. **Build** — implement exactly one module
2. **Test** — write pytest coverage immediately
3. **Learn** — run tests, fix failures
4. **Confirm** — review before proceeding to the next component

## Commit Messages

Use imperative mood, concise summary line (<72 chars), optional body for rationale:

```
Add Groq LLM provider adapter with factory

Implements LLMProvider port using langchain-groq. Default provider
when LLM_PROVIDER=groq in environment.
```

## Security

- Never commit API keys; use `.env` (gitignored) and `.env.example` templates
- Do not log full LLM API keys or raw prompt secrets in request logs
- Ticket history lookups must enforce customer scope

## File Layout for New Code

When adding a new port:

1. Define abstract interface in `src/domain/ports/`
2. Implement adapter in `src/infrastructure/`
3. Wire in factory/DI in `src/api/dependencies.py`
4. Add unit tests with mocked adapter

from __future__ import annotations

from functools import lru_cache

from agent.adapter import LangGraphSupportAgentAdapter
from domain.ports import LLMProvider, MCPToolClient, RequestLogger, VectorStore
from domain.ports.document_repository import DocumentRepository
from domain.ports.support_agent import SupportAgent
from infrastructure.config.settings import Settings, get_settings
from infrastructure.documents.markdown_repository import MarkdownDocumentRepository
from infrastructure.llm.embeddings import create_embedding_provider
from infrastructure.llm.providers import create_llm_provider
from infrastructure.logging.file_request_logger import FileRequestLogger
from infrastructure.mcp.direct_client import DirectMCPToolClient
from infrastructure.vector_store.pgvector_store import PgVectorStore
from mcp_server.tools.registry import ToolRegistry
from use_cases.ingest_documents import IngestDocumentsUseCase
from use_cases.investigate_ticket import InvestigateTicketUseCase


@lru_cache
def get_llm_provider() -> LLMProvider:
    return create_llm_provider(get_settings())


@lru_cache
def get_vector_store() -> VectorStore:
    return PgVectorStore(get_settings())


@lru_cache
def get_document_repository() -> DocumentRepository:
    return MarkdownDocumentRepository()


@lru_cache
def get_tool_registry() -> ToolRegistry:
    settings = get_settings()
    return ToolRegistry(
        settings,
        vector_store=get_vector_store(),
        embedding_provider=create_embedding_provider(settings),
    )


@lru_cache
def get_mcp_client() -> MCPToolClient:
    return DirectMCPToolClient(get_tool_registry())


@lru_cache
def get_request_logger() -> RequestLogger:
    return FileRequestLogger(get_settings())


@lru_cache
def get_support_agent() -> SupportAgent:
    settings = get_settings()
    return LangGraphSupportAgentAdapter(
        get_llm_provider(),
        get_mcp_client(),
        settings,
    )


def get_investigate_use_case() -> InvestigateTicketUseCase:
    return InvestigateTicketUseCase(get_support_agent(), get_request_logger())


def get_ingest_use_case() -> IngestDocumentsUseCase:
    settings = get_settings()
    return IngestDocumentsUseCase(
        get_document_repository(),
        create_embedding_provider(settings),
        get_vector_store(),
        settings,
    )

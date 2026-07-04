from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel

from domain.entities.models import DocumentChunk, ResolutionReport

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    @abstractmethod
    async def invoke(self, prompt: str, system: str | None = None) -> str:
        """Return free-form LLM text response."""

    @abstractmethod
    async def invoke_structured(
        self,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        """Return structured output parsed into the given Pydantic schema."""


class VectorStore(ABC):
    @abstractmethod
    async def add_documents(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> int:
        """Persist document chunks with embeddings. Returns count inserted."""

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[DocumentChunk]:
        """Return top-k similar document chunks."""

    @abstractmethod
    async def count_documents(self) -> int:
        """Return total number of stored chunks."""


class MCPToolClient(ABC):
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        """Invoke an MCP tool and return its result payload."""


class RequestLogger(ABC):
    @abstractmethod
    def start_request(self, request_id: str, input_data: dict[str, object]) -> None:
        """Begin logging for a request."""

    @abstractmethod
    def log_decision(
        self,
        request_id: str,
        node: str,
        input_summary: str,
        output_summary: str,
        duration_ms: int,
    ) -> None:
        """Record an agent node decision."""

    @abstractmethod
    def log_tool_call(
        self,
        request_id: str,
        tool: str,
        parameters: dict[str, object],
        result: dict[str, object],
        success: bool,
    ) -> None:
        """Record an MCP tool invocation."""

    @abstractmethod
    def complete_request(
        self,
        request_id: str,
        output: ResolutionReport,
        elapsed_ms: int,
    ) -> None:
        """Finalize and persist the request log."""

    @abstractmethod
    def get_log_path(self, request_id: str) -> str:
        """Return filesystem path for the request log file."""


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for input texts."""

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Return embedding vector for a search query."""

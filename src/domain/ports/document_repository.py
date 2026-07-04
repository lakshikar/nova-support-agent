from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.models import DocumentChunk


class DocumentRepository(ABC):
    @abstractmethod
    def load_raw_documents(self, docs_path: str) -> list[tuple[str, str]]:
        """Load raw markdown documents. Returns list of (filename, content)."""

    @abstractmethod
    def chunk_document(self, filename: str, content: str) -> list[DocumentChunk]:
        """Split a document into searchable chunks."""

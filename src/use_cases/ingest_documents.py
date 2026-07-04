from __future__ import annotations

from domain.entities.models import DocumentChunk
from domain.ports import EmbeddingProvider, VectorStore
from domain.ports.document_repository import DocumentRepository
from infrastructure.config.settings import Settings


class IngestDocumentsUseCase:
    """Load, chunk, embed, and store NovaTech documentation."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        settings: Settings,
    ) -> None:
        self._document_repo = document_repo
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._settings = settings

    async def execute(self, force: bool = False) -> int:
        existing = await self._vector_store.count_documents()
        if existing > 0 and not force:
            return existing

        documents = self._document_repo.load_raw_documents(self._settings.docs_path)
        all_chunks: list[DocumentChunk] = []
        for filename, content in documents:
            all_chunks.extend(self._document_repo.chunk_document(filename, content))

        if not all_chunks:
            return 0

        texts = [chunk.content for chunk in all_chunks]
        embeddings = await self._embedding_provider.embed_texts(texts)
        await self._vector_store.add_documents(all_chunks, embeddings)
        return len(all_chunks)

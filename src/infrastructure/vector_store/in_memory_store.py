from __future__ import annotations

import math

from domain.entities.models import DocumentChunk
from domain.ports import VectorStore


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store for unit tests."""

    def __init__(self) -> None:
        self._chunks: list[tuple[DocumentChunk, list[float]]] = []

    async def add_documents(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> int:
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._chunks.append((chunk, embedding))
        return len(chunks)

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[DocumentChunk]:
        scored: list[tuple[float, DocumentChunk]] = []
        for chunk, embedding in self._chunks:
            if source_filter and chunk.source_file != source_filter:
                continue
            score = _cosine_similarity(query_embedding, embedding)
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            DocumentChunk(
                content=chunk.content,
                source_file=chunk.source_file,
                section=chunk.section,
                score=score,
                metadata=chunk.metadata,
            )
            for score, chunk in scored[:top_k]
        ]

    async def count_documents(self) -> int:
        return len(self._chunks)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

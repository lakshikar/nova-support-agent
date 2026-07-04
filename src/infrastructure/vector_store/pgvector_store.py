from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Column, Integer, String, Text, create_engine, func, select, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from domain.entities.models import DocumentChunk
from domain.ports import VectorStore
from infrastructure.config.settings import Settings


class Base(DeclarativeBase):
    pass


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    source_file = Column(String(255), nullable=False)
    section = Column(String(512), nullable=False)
    metadata_json = Column(Text, default="{}")


class PgVectorStore(VectorStore):
    """PostgreSQL + pgvector document store."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = create_engine(settings.database_url)
        self._session_factory = sessionmaker(bind=self._engine)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        dimensions = self._settings.embedding_dimensions
        with self._engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            Base.metadata.create_all(conn)
            conn.execute(
                text(
                    f"""
                    ALTER TABLE document_chunks
                    ADD COLUMN IF NOT EXISTS embedding_vec vector({dimensions})
                    """
                )
            )

    async def add_documents(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> int:
        with self._engine.begin() as conn:
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                vec_literal = "[" + ",".join(str(v) for v in embedding) + "]"
                result = conn.execute(
                    text(
                        """
                        INSERT INTO document_chunks
                            (content, source_file, section, metadata_json, embedding_vec)
                        VALUES
                            (:content, :source_file, :section, :metadata_json, CAST(:vec AS vector))
                        RETURNING id
                        """
                    ),
                    {
                        "content": chunk.content,
                        "source_file": chunk.source_file,
                        "section": chunk.section,
                        "metadata_json": json.dumps(chunk.metadata),
                        "vec": vec_literal,
                    },
                )
                result.fetchone()
        return len(chunks)

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[DocumentChunk]:
        vec_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"
        params: dict[str, Any] = {"vec": vec_literal, "top_k": top_k}
        filter_clause = ""
        if source_filter:
            filter_clause = "AND source_file = :source_filter"
            params["source_filter"] = source_filter

        query_sql = f"""
            SELECT content, source_file, section,
                   1 - (embedding_vec <=> CAST(:vec AS vector)) AS score
            FROM document_chunks
            WHERE embedding_vec IS NOT NULL
            {filter_clause}
            ORDER BY embedding_vec <=> CAST(:vec AS vector)
            LIMIT :top_k
        """
        with self._engine.connect() as conn:
            rows = conn.execute(text(query_sql), params).fetchall()

        return [
            DocumentChunk(
                content=row.content,
                source_file=row.source_file,
                section=row.section,
                score=float(row.score) if row.score is not None else 0.0,
            )
            for row in rows
        ]

    async def count_documents(self) -> int:
        with Session(self._engine) as session:
            count = session.scalar(select(func.count()).select_from(DocumentChunkModel))
            return int(count or 0)

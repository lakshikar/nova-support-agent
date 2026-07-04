from __future__ import annotations

import re
from pathlib import Path

from domain.entities.models import DocumentChunk
from domain.ports.document_repository import DocumentRepository


class MarkdownDocumentRepository(DocumentRepository):
    """Load and chunk NovaTech markdown documentation."""

    def load_raw_documents(self, docs_path: str) -> list[tuple[str, str]]:
        path = Path(docs_path)
        documents: list[tuple[str, str]] = []
        for file_path in sorted(path.glob("*.md")):
            documents.append((file_path.name, file_path.read_text(encoding="utf-8")))
        return documents

    def chunk_document(self, filename: str, content: str) -> list[DocumentChunk]:
        sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
        chunks: list[DocumentChunk] = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            header_match = re.match(r"^## (.+)$", section, flags=re.MULTILINE)
            section_title = header_match.group(1).strip() if header_match else "Introduction"
            for part in self._split_by_size(section, max_chars=2000):
                chunks.append(
                    DocumentChunk(
                        content=part,
                        source_file=filename,
                        section=section_title,
                        metadata={"source_file": filename, "section": section_title},
                    )
                )
        return chunks

    def _split_by_size(self, text: str, max_chars: int) -> list[str]:
        if len(text) <= max_chars:
            return [text]
        parts: list[str] = []
        paragraphs = text.split("\n\n")
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    parts.append(current)
                current = paragraph
        if current:
            parts.append(current)
        return parts

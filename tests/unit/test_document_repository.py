from __future__ import annotations

from infrastructure.documents.markdown_repository import MarkdownDocumentRepository


def test_chunk_document_splits_on_headers() -> None:
    repo = MarkdownDocumentRepository()
    content = """# Title

Intro paragraph.

## Section One

Content for section one.

## Section Two

Content for section two.
"""
    chunks = repo.chunk_document("test.md", content)
    assert len(chunks) >= 2
    sections = {chunk.section for chunk in chunks}
    assert "Section One" in sections
    assert "Section Two" in sections


def test_load_raw_documents_from_data_dir() -> None:
    repo = MarkdownDocumentRepository()
    docs = repo.load_raw_documents("data/raw_docs")
    assert len(docs) >= 8
    filenames = [name for name, _ in docs]
    assert "troubleshooting-guide.md" in filenames

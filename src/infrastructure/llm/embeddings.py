from __future__ import annotations

import httpx

from domain.ports import EmbeddingProvider
from infrastructure.config.settings import Settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        from langchain_openai import OpenAIEmbeddings

        self._embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._embeddings.aembed_documents(texts)

    async def embed_query(self, query: str) -> list[float]:
        return await self._embeddings.aembed_query(query)


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_embedding_model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_query(text) for text in texts]

    async def embed_query(self, query: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": query},
            )
            response.raise_for_status()
            return response.json()["embedding"]


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "openai":
        return OpenAIEmbeddingProvider(settings)
    if provider == "ollama":
        return OllamaEmbeddingProvider(settings)
    raise ValueError(f"Unsupported embedding provider: {provider}")

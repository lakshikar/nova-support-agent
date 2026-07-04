from __future__ import annotations

import asyncio
import time

import httpx

from domain.ports import EmbeddingProvider
from infrastructure.config.settings import Settings


class NvidiaEmbeddingProvider(EmbeddingProvider):
    """NVIDIA NIM — OpenAI-compatible embeddings API (nv-embed-v1, 4096 dims)."""

    # NVIDIA free tier: 40 rpm — cap at 29 to stay safely under 30 rpm.
    MAX_REQUESTS_PER_MINUTE = 29
    MIN_REQUEST_INTERVAL_SEC = 60.0 / MAX_REQUESTS_PER_MINUTE

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.nvidia_api_key
        self._base_url = settings.nvidia_base_url.rstrip("/")
        self._model = settings.nvidia_embedding_model
        self._last_request_at: float | None = None
        self._rate_limit_lock = asyncio.Lock()

    async def _wait_for_rate_limit(self) -> None:
        async with self._rate_limit_lock:
            if self._last_request_at is not None:
                elapsed = time.monotonic() - self._last_request_at
                wait_seconds = self.MIN_REQUEST_INTERVAL_SEC - elapsed
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
            self._last_request_at = time.monotonic()

    async def _post_embedding(
        self,
        client: httpx.AsyncClient,
        text: str,
        input_type: str,
    ) -> list[float]:
        await self._wait_for_rate_limit()
        response = await client.post(
            f"{self._base_url}/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "input": [text],
                "model": self._model,
                "encoding_format": "float",
                "input_type": input_type,
                "truncate": "NONE",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def _embed_batch(self, inputs: list[str], input_type: str) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            embeddings: list[list[float]] = []
            for text in inputs:
                embeddings.append(await self._post_embedding(client, text, input_type))
            return embeddings

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Documents indexed as passages for retrieval.
        return await self._embed_batch(texts, input_type="passage")

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await self._embed_batch([query], input_type="query")
        return embeddings[0]


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
    if provider == "nvidia":
        return NvidiaEmbeddingProvider(settings)
    if provider == "openai":
        return OpenAIEmbeddingProvider(settings)
    if provider == "ollama":
        return OllamaEmbeddingProvider(settings)
    raise ValueError(f"Unsupported embedding provider: {provider}")

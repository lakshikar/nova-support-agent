from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.config.settings import Settings
from infrastructure.llm.embeddings import (
    NvidiaEmbeddingProvider,
    OpenAIEmbeddingProvider,
    create_embedding_provider,
)


def test_create_embedding_provider_nvidia() -> None:
    settings = Settings(embedding_provider="nvidia", nvidia_api_key="test-key")
    provider = create_embedding_provider(settings)
    assert isinstance(provider, NvidiaEmbeddingProvider)


def test_create_embedding_provider_openai() -> None:
    settings = Settings(embedding_provider="openai", openai_api_key="test-key")
    provider = create_embedding_provider(settings)
    assert isinstance(provider, OpenAIEmbeddingProvider)


def test_create_embedding_provider_invalid() -> None:
    settings = Settings(embedding_provider="invalid")
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        create_embedding_provider(settings)


@pytest.mark.asyncio
async def test_nvidia_embed_query_uses_query_input_type() -> None:
    provider = NvidiaEmbeddingProvider(
        Settings(nvidia_api_key="test-key", nvidia_embedding_model="nvidia/nv-embed-v1")
    )
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2]}]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        result = await provider.embed_query("test query")

    assert result == [0.1, 0.2]
    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["json"]["input_type"] == "query"
    assert call_kwargs["json"]["input"] == ["test query"]


@pytest.mark.asyncio
async def test_nvidia_embed_texts_uses_passage_input_type() -> None:
    provider = NvidiaEmbeddingProvider(
        Settings(nvidia_api_key="test-key", nvidia_embedding_model="nvidia/nv-embed-v1")
    )
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.1]}]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        result = await provider.embed_texts(["doc one", "doc two"])

    assert len(result) == 2
    assert mock_client.post.call_count == 2
    first_call_kwargs = mock_client.post.call_args_list[0].kwargs
    assert first_call_kwargs["json"]["input_type"] == "passage"
    assert first_call_kwargs["json"]["input"] == ["doc one"]


@pytest.mark.asyncio
async def test_nvidia_rate_limits_between_posts() -> None:
    provider = NvidiaEmbeddingProvider(
        Settings(nvidia_api_key="test-key", nvidia_embedding_model="nvidia/nv-embed-v1")
    )
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.1]}]}
    mock_response.raise_for_status = MagicMock()

    monotonic_values = iter([0.0, 0.5, 0.5])
    sleep_calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    with (
        patch("httpx.AsyncClient") as mock_client_cls,
        patch("infrastructure.llm.embeddings.time.monotonic", side_effect=monotonic_values),
        patch("infrastructure.llm.embeddings.asyncio.sleep", side_effect=fake_sleep),
    ):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        await provider.embed_texts(["doc one", "doc two"])

    assert mock_client.post.call_count == 2
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(
        NvidiaEmbeddingProvider.MIN_REQUEST_INTERVAL_SEC - 0.5,
        rel=1e-3,
    )

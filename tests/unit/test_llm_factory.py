from __future__ import annotations

import pytest

from infrastructure.config.settings import Settings
from infrastructure.llm.providers import (
    GroqLLMProvider,
    NvidiaLLMProvider,
    OllamaLLMProvider,
    OpenAILLMProvider,
    create_llm_provider,
)


def test_create_llm_provider_nvidia() -> None:
    settings = Settings(llm_provider="nvidia", nvidia_api_key="test-key")
    provider = create_llm_provider(settings)
    assert isinstance(provider, NvidiaLLMProvider)


def test_create_llm_provider_groq() -> None:
    settings = Settings(llm_provider="groq", groq_api_key="test-key")
    provider = create_llm_provider(settings)
    assert isinstance(provider, GroqLLMProvider)


def test_create_llm_provider_openai() -> None:
    settings = Settings(llm_provider="openai", openai_api_key="test-key")
    provider = create_llm_provider(settings)
    assert isinstance(provider, OpenAILLMProvider)


def test_create_llm_provider_ollama() -> None:
    settings = Settings(llm_provider="ollama")
    provider = create_llm_provider(settings)
    assert isinstance(provider, OllamaLLMProvider)


def test_create_llm_provider_invalid() -> None:
    settings = Settings(llm_provider="invalid")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm_provider(settings)


def test_settings_default_to_nvidia() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "nvidia"
    assert settings.embedding_provider == "nvidia"
    assert settings.embedding_dimensions == 4096

from __future__ import annotations

import pytest

from domain.entities.models import InvestigationPlan
from infrastructure.config.settings import Settings
from infrastructure.llm.providers import (
    GroqLLMProvider,
    LangChainLLMProvider,
    NvidiaLLMProvider,
    OllamaLLMProvider,
    OpenAILLMProvider,
    create_llm_provider,
)


def test_create_llm_provider_nvidia() -> None:
    settings = Settings(llm_provider="nvidia", nvidia_api_key="test-key")
    provider = create_llm_provider(settings)
    assert isinstance(provider, NvidiaLLMProvider)
    assert provider._structured_output_mode == "prompt_json"


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


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.llm_provider == "groq"
    assert settings.embedding_provider == "nvidia"
    assert settings.embedding_dimensions == 4096


def test_build_messages_adds_json_hint_for_structured_output() -> None:
    messages = LangChainLLMProvider._build_messages(
        "Analyze the ticket.",
        system="You are a support agent.",
        require_json_keyword=True,
    )
    assert len(messages) == 2
    assert "json" in str(messages[0].content).lower()


def test_build_messages_skips_json_hint_when_already_present() -> None:
    messages = LangChainLLMProvider._build_messages(
        "Return JSON output.",
        system="You are a support agent.",
        require_json_keyword=True,
    )
    assert messages[0].content == "You are a support agent."


def test_structured_fallback_prompt_includes_nested_schema_fields() -> None:
    schema = InvestigationPlan.model_json_schema()
    assert "rationale" in str(schema)
    assert "InvestigationStep" in str(schema)

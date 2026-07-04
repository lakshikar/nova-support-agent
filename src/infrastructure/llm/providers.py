from __future__ import annotations

import json
from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from domain.ports import LLMProvider
from infrastructure.config.settings import Settings

T = TypeVar("T", bound=BaseModel)


class LangChainLLMProvider(LLMProvider):
    """Base adapter wrapping LangChain chat models."""

    def __init__(self, chat_model: object) -> None:
        self._chat = chat_model

    async def invoke(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        response = await self._chat.ainvoke(messages)
        return str(response.content)

    async def invoke_structured(
        self,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        structured = self._chat.with_structured_output(schema)
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        result = await structured.ainvoke(messages)
        if isinstance(result, schema):
            return result
        if isinstance(result, dict):
            return schema.model_validate(result)
        raise ValueError(f"Unexpected structured output type: {type(result)}")


class GroqLLMProvider(LangChainLLMProvider):
    def __init__(self, settings: Settings) -> None:
        chat = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.1,
        )
        super().__init__(chat)


class OpenAILLMProvider(LangChainLLMProvider):
    def __init__(self, settings: Settings) -> None:
        chat = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.1,
        )
        super().__init__(chat)


class OllamaLLMProvider(LangChainLLMProvider):
    def __init__(self, settings: Settings) -> None:
        chat = ChatOpenAI(
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
            model=settings.ollama_model,
            temperature=0.1,
        )
        super().__init__(chat)


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "groq":
        return GroqLLMProvider(settings)
    if provider == "openai":
        return OpenAILLMProvider(settings)
    if provider == "ollama":
        return OllamaLLMProvider(settings)
    raise ValueError(f"Unsupported LLM provider: {provider}")

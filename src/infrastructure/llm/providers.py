from __future__ import annotations

import json
import logging
import re
from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from domain.ports import LLMProvider
from infrastructure.config.settings import Settings

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

LLM_REQUEST_TIMEOUT_SEC = 120.0
LLM_MAX_RETRIES = 2


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
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        structured = self._chat.with_structured_output(schema, method="json_mode")
        try:
            result = await structured.ainvoke(messages)
            return self._coerce_structured(result, schema)
        except Exception as exc:
            logger.warning(
                "Structured json_mode failed for %s (%s); using JSON parse fallback",
                schema.__name__,
                exc,
            )
            return await self._invoke_structured_fallback(prompt, schema, system)

    def _coerce_structured(self, result: object, schema: type[T]) -> T:
        if isinstance(result, schema):
            return result
        if isinstance(result, dict):
            return schema.model_validate(result)
        raise ValueError(f"Unexpected structured output type: {type(result)}")

    async def _invoke_structured_fallback(
        self,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        json_prompt = (
            f"{prompt}\n\n"
            "Respond with a single JSON object only (no markdown fences) "
            "containing all required fields."
        )
        raw = await self.invoke(json_prompt, system=system)
        payload = self._extract_json(raw)
        return schema.model_validate(payload)

    @staticmethod
    def _extract_json(raw: str) -> dict[str, object]:
        text = raw.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object found in LLM response: {raw[:200]}")
        return json.loads(text[start : end + 1])


class GroqLLMProvider(LangChainLLMProvider):
    def __init__(self, settings: Settings) -> None:
        chat = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.1,
            timeout=LLM_REQUEST_TIMEOUT_SEC,
            max_retries=LLM_MAX_RETRIES,
        )
        super().__init__(chat)


class OpenAILLMProvider(LangChainLLMProvider):
    def __init__(self, settings: Settings) -> None:
        chat = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.1,
            timeout=LLM_REQUEST_TIMEOUT_SEC,
            max_retries=LLM_MAX_RETRIES,
        )
        super().__init__(chat)


class OllamaLLMProvider(LangChainLLMProvider):
    def __init__(self, settings: Settings) -> None:
        chat = ChatOpenAI(
            base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
            model=settings.ollama_model,
            temperature=0.1,
            timeout=LLM_REQUEST_TIMEOUT_SEC,
            max_retries=LLM_MAX_RETRIES,
        )
        super().__init__(chat)


class NvidiaLLMProvider(LangChainLLMProvider):
    """NVIDIA NIM — OpenAI-compatible chat API."""

    def __init__(self, settings: Settings) -> None:
        chat = ChatOpenAI(
            base_url=settings.nvidia_base_url.rstrip("/"),
            api_key=settings.nvidia_api_key,
            model=settings.nvidia_model,
            temperature=0.2,
            timeout=LLM_REQUEST_TIMEOUT_SEC,
            max_retries=LLM_MAX_RETRIES,
        )
        super().__init__(chat)


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "nvidia":
        return NvidiaLLMProvider(settings)
    if provider == "groq":
        return GroqLLMProvider(settings)
    if provider == "openai":
        return OpenAILLMProvider(settings)
    if provider == "ollama":
        return OllamaLLMProvider(settings)
    raise ValueError(f"Unsupported LLM provider: {provider}")

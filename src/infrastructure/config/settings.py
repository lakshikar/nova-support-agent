from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "nvidia"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.3-70b-instruct"
    nvidia_embedding_model: str = "nvidia/nv-embed-v1"

    embedding_provider: str = "nvidia"
    embedding_dimensions: int = 4096
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_embedding_model: str = "nomic-embed-text"

    database_url: str = "postgresql+psycopg://nova:nova@localhost:5432/nova_support"
    docs_path: str = "data/raw_docs"
    ticket_history_path: str = "data/ticket-history.json"
    sla_policy_path: str = "data/raw_docs/sla-policy.md"
    logs_path: str = "logs"
    mcp_server_url: str = "http://localhost:8081/mcp"

    max_agent_iterations: int = 8
    default_timezone: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    return Settings()

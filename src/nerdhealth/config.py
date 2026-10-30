"""Settings, read from environment variables (and a git-ignored .env for local work)."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM, behind ModelGateway. Groq exposes an OpenAI-compatible API.
    groq_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-20b"
    llm_max_retries: int = 5
    llm_backoff_seconds: float = 1.0
    # Price per million tokens, as shown in the provider console. None = unknown, never 0.
    llm_price_in_per_mtok: float | None = None
    llm_price_out_per_mtok: float | None = None

    qdrant_url: str = "http://localhost:6333"
    database_url: str = "postgresql://nerdhealth:nerdhealth@localhost:5432/nerdhealth"

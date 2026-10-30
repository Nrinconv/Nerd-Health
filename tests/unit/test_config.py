from __future__ import annotations

import pytest
from pydantic import SecretStr

from nerdhealth.config import Settings


def test_defaults_load_without_any_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GROQ_API_KEY", "LLM_MODEL", "DATABASE_URL", "QDRANT_URL", "LLM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.groq_api_key is None
    assert settings.llm_base_url == "https://api.groq.com/openai/v1"
    assert settings.llm_model == "openai/gpt-oss-20b"
    assert settings.qdrant_url.startswith("http://")
    assert settings.database_url.startswith("postgresql://")


def test_values_come_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant.example:6333")
    settings = Settings(_env_file=None)
    assert settings.llm_model == "openai/gpt-oss-120b"
    assert settings.qdrant_url == "http://qdrant.example:6333"


def test_api_key_is_secret_and_never_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "not-a-real-key")
    settings = Settings(_env_file=None)
    assert isinstance(settings.groq_api_key, SecretStr)
    assert settings.groq_api_key.get_secret_value() == "not-a-real-key"
    assert "not-a-real-key" not in repr(settings)
    assert "not-a-real-key" not in str(settings)

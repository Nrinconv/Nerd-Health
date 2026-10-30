"""The single door to the language model."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import openai

from nerdhealth.config import Settings

Message = dict[str, str]


class GatewayError(Exception):
    """The model could not be reached or refused the request."""


@dataclass(frozen=True)
class Completion:
    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: float | None  # None when no price is configured; never 0 by default


class ModelGateway(Protocol):
    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> Completion: ...


class FakeGateway:
    """Replays canned responses, for tests."""

    def __init__(self, responses: Sequence[str]) -> None:
        self._responses = list(responses)

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> Completion:
        if not self._responses:
            raise GatewayError("FakeGateway has no responses left")
        return Completion(self._responses.pop(0), tokens_in=0, tokens_out=0, cost_usd=None)


class OpenAICompatibleGateway:
    """Any OpenAI-compatible endpoint (Groq, or a self-hosted server), chosen by config."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: Any = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if settings.groq_api_key is None:
            raise GatewayError("GROQ_API_KEY is not set; put it in .env or the environment")
        self._settings = settings
        self._sleep = sleep
        # Retries are ours, so they are bounded and visible; the client must not add its own.
        self._client = openai.OpenAI(
            api_key=settings.groq_api_key.get_secret_value(),
            base_url=settings.llm_base_url,
            max_retries=0,
            http_client=http_client,
        )

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> Completion:
        response = self._request(messages, max_tokens)
        usage = response.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0
        return Completion(
            text=response.choices[0].message.content or "",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=self._cost(tokens_in, tokens_out),
        )

    def _request(self, messages: Sequence[Message], max_tokens: int) -> Any:
        delay = self._settings.llm_backoff_seconds
        for attempt in range(self._settings.llm_max_retries + 1):
            try:
                return self._client.chat.completions.create(
                    model=self._settings.llm_model,
                    messages=list(messages),  # type: ignore[arg-type]
                    max_tokens=max_tokens,
                )
            except openai.RateLimitError as exc:
                if attempt == self._settings.llm_max_retries:
                    raise GatewayError("rate limit: retries exhausted") from exc
                self._sleep(delay)
                delay *= 2
            except openai.OpenAIError as exc:
                raise GatewayError(f"model request failed: {exc}") from exc
        raise AssertionError("unreachable")

    def _cost(self, tokens_in: int, tokens_out: int) -> float | None:
        price_in = self._settings.llm_price_in_per_mtok
        price_out = self._settings.llm_price_out_per_mtok
        if price_in is None or price_out is None:
            return None
        return (tokens_in * price_in + tokens_out * price_out) / 1_000_000

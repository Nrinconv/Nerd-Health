from __future__ import annotations

import httpx
import openai
import pytest
import respx
from pydantic import SecretStr

from nerdhealth.config import Settings
from nerdhealth.gateway import (
    Completion,
    FakeGateway,
    GatewayError,
    ModelGateway,
    OpenAICompatibleGateway,
)

URL = "https://llm.test/v1/chat/completions"
MESSAGES = [{"role": "user", "content": "hello"}]


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "groq_api_key": SecretStr("test-key"),
        "llm_base_url": "https://llm.test/v1",
        "llm_model": "test-model",
        "llm_max_retries": 2,
        "llm_backoff_seconds": 0.5,
    }
    return Settings(_env_file=None, **{**base, **overrides})  # type: ignore[arg-type]


def _ok(text: str = "hi", tokens_in: int = 10, tokens_out: int = 4) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": text},
                }
            ],
            "usage": {
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
                "total_tokens": tokens_in + tokens_out,
            },
        },
    )


def test_fake_gateway_satisfies_the_interface_and_replays_responses() -> None:
    gateway: ModelGateway = FakeGateway(["one", "two"])
    assert gateway.complete(MESSAGES, max_tokens=10).text == "one"
    assert gateway.complete(MESSAGES, max_tokens=10).text == "two"


def test_fake_gateway_fails_loudly_when_responses_run_out() -> None:
    gateway = FakeGateway([])
    with pytest.raises(GatewayError):
        gateway.complete(MESSAGES, max_tokens=10)


@respx.mock
def test_complete_returns_text_and_token_counts() -> None:
    respx.post(URL).mock(return_value=_ok("answer", 12, 5))
    result = OpenAICompatibleGateway(_settings()).complete(MESSAGES, max_tokens=50)
    assert isinstance(result, Completion)
    assert result.text == "answer"
    assert (result.tokens_in, result.tokens_out) == (12, 5)


@respx.mock
def test_cost_is_missing_not_zero_when_no_price_is_configured() -> None:
    respx.post(URL).mock(return_value=_ok())
    result = OpenAICompatibleGateway(_settings()).complete(MESSAGES, max_tokens=50)
    assert result.cost_usd is None


@respx.mock
def test_cost_is_computed_from_configured_price_per_million_tokens() -> None:
    respx.post(URL).mock(return_value=_ok(tokens_in=1_000_000, tokens_out=500_000))
    settings = _settings(llm_price_in_per_mtok=0.10, llm_price_out_per_mtok=0.50)
    result = OpenAICompatibleGateway(settings).complete(MESSAGES, max_tokens=50)
    assert result.cost_usd == pytest.approx(0.10 + 0.25)


@respx.mock
def test_rate_limit_is_retried_with_exponential_backoff() -> None:
    route = respx.post(URL).mock(
        side_effect=[httpx.Response(429, json={"error": {"message": "slow down"}}), _ok("late")]
    )
    sleeps: list[float] = []
    gateway = OpenAICompatibleGateway(_settings(), sleep=sleeps.append)
    assert gateway.complete(MESSAGES, max_tokens=50).text == "late"
    assert route.call_count == 2
    assert sleeps == [0.5]


@respx.mock
def test_backoff_doubles_between_attempts() -> None:
    respx.post(URL).mock(side_effect=[httpx.Response(429), httpx.Response(429), _ok("third")])
    sleeps: list[float] = []
    gateway = OpenAICompatibleGateway(_settings(), sleep=sleeps.append)
    assert gateway.complete(MESSAGES, max_tokens=50).text == "third"
    assert sleeps == [0.5, 1.0]


@respx.mock
def test_gives_up_after_max_retries_instead_of_looping() -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(429))
    gateway = OpenAICompatibleGateway(_settings(), sleep=lambda _s: None)
    with pytest.raises(GatewayError):
        gateway.complete(MESSAGES, max_tokens=50)
    assert route.call_count == 3  # first try + llm_max_retries


@respx.mock
def test_non_rate_limit_errors_are_not_retried() -> None:
    route = respx.post(URL).mock(
        return_value=httpx.Response(401, json={"error": {"message": "no"}})
    )
    gateway = OpenAICompatibleGateway(_settings(), sleep=lambda _s: None)
    with pytest.raises(GatewayError) as info:
        gateway.complete(MESSAGES, max_tokens=50)
    assert route.call_count == 1
    assert isinstance(info.value.__cause__, openai.AuthenticationError)


def test_missing_api_key_is_a_clear_error_not_a_network_call() -> None:
    with pytest.raises(GatewayError, match="GROQ_API_KEY"):
        OpenAICompatibleGateway(_settings(groq_api_key=None))

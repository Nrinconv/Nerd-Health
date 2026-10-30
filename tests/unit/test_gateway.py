from __future__ import annotations

import httpx2
import openai
import pytest
from pydantic import SecretStr

from nerdhealth.config import Settings
from nerdhealth.gateway import (
    Completion,
    FakeGateway,
    GatewayError,
    ModelGateway,
    OpenAICompatibleGateway,
)

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


def _ok(text: str = "hi", tokens_in: int = 10, tokens_out: int = 4) -> httpx2.Response:
    return httpx2.Response(
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


class Script:
    """A scripted HTTP endpoint: replays responses in order and counts calls."""

    def __init__(self, *responses: httpx2.Response) -> None:
        self._responses = list(responses)
        self.call_count = 0

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.call_count += 1
        # The last response repeats, so "always 429" needs a single entry.
        return self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]

    def client(self) -> httpx2.Client:
        return httpx2.Client(transport=httpx2.MockTransport(self))


def _gateway(
    script: Script, sleeps: list[float] | None = None, **overrides: object
) -> OpenAICompatibleGateway:
    sink = sleeps if sleeps is not None else []
    return OpenAICompatibleGateway(
        _settings(**overrides), http_client=script.client(), sleep=sink.append
    )


def test_fake_gateway_satisfies_the_interface_and_replays_responses() -> None:
    gateway: ModelGateway = FakeGateway(["one", "two"])
    assert gateway.complete(MESSAGES, max_tokens=10).text == "one"
    assert gateway.complete(MESSAGES, max_tokens=10).text == "two"


def test_fake_gateway_fails_loudly_when_responses_run_out() -> None:
    gateway = FakeGateway([])
    with pytest.raises(GatewayError):
        gateway.complete(MESSAGES, max_tokens=10)


def test_complete_returns_text_and_token_counts() -> None:
    result = _gateway(Script(_ok("answer", 12, 5))).complete(MESSAGES, max_tokens=50)
    assert isinstance(result, Completion)
    assert result.text == "answer"
    assert (result.tokens_in, result.tokens_out) == (12, 5)


def test_cost_is_missing_not_zero_when_no_price_is_configured() -> None:
    result = _gateway(Script(_ok())).complete(MESSAGES, max_tokens=50)
    assert result.cost_usd is None


def test_cost_is_computed_from_configured_price_per_million_tokens() -> None:
    script = Script(_ok(tokens_in=1_000_000, tokens_out=500_000))
    gateway = _gateway(script, llm_price_in_per_mtok=0.10, llm_price_out_per_mtok=0.50)
    assert gateway.complete(MESSAGES, max_tokens=50).cost_usd == pytest.approx(0.10 + 0.25)


def test_rate_limit_is_retried_with_exponential_backoff() -> None:
    script = Script(httpx2.Response(429, json={"error": {"message": "slow down"}}), _ok("late"))
    sleeps: list[float] = []
    assert _gateway(script, sleeps).complete(MESSAGES, max_tokens=50).text == "late"
    assert script.call_count == 2
    assert sleeps == [0.5]


def test_backoff_doubles_between_attempts() -> None:
    script = Script(httpx2.Response(429), httpx2.Response(429), _ok("third"))
    sleeps: list[float] = []
    assert _gateway(script, sleeps).complete(MESSAGES, max_tokens=50).text == "third"
    assert sleeps == [0.5, 1.0]


def test_gives_up_after_max_retries_instead_of_looping() -> None:
    script = Script(httpx2.Response(429))
    with pytest.raises(GatewayError):
        _gateway(script).complete(MESSAGES, max_tokens=50)
    assert script.call_count == 3  # first try + llm_max_retries


def test_non_rate_limit_errors_are_not_retried() -> None:
    script = Script(httpx2.Response(401, json={"error": {"message": "no"}}))
    with pytest.raises(GatewayError) as info:
        _gateway(script).complete(MESSAGES, max_tokens=50)
    assert script.call_count == 1
    assert isinstance(info.value.__cause__, openai.AuthenticationError)


def test_missing_api_key_is_a_clear_error_not_a_network_call() -> None:
    with pytest.raises(GatewayError, match="GROQ_API_KEY"):
        OpenAICompatibleGateway(_settings(groq_api_key=None))

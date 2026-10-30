# Architecture

## Language model

All model calls go through `ModelGateway` (`src/nerdhealth/gateway.py`). The one implementation,
`OpenAICompatibleGateway`, speaks the OpenAI chat API, so the provider is a config change
(`LLM_BASE_URL`, `LLM_MODEL`), not a code change.

**Provider:** Groq, free plan during development. **Candidates**, kept by config and compared
on the golden sets from Stage 1; the cheapest that meets the §3.3 thresholds wins:

| Model | Role | Price in / out per 1M tokens | Source |
|---|---|---|---|
| `openai/gpt-oss-20b` (default) | small, cheap candidate | **not yet recorded** | Groq console, to be filled on the day it is chosen |
| `openai/gpt-oss-120b` | stronger candidate for synthesis and grounding | **not yet recorded** | same |

Until a price is set (`LLM_PRICE_IN_PER_MTOK` / `LLM_PRICE_OUT_PER_MTOK`), the gateway reports
cost as missing (`None`), never as 0.

**Free-plan limits** (check the account's exact values at console.groq.com/settings/limits):
about 30 requests/min, 1,000 requests/day, 8K tokens/min, 200K tokens/day per model, and 8K
tokens per request. Consequences: prompts stay tight; batch jobs run in small paced batches;
the gateway retries HTTP 429 with exponential back-off, bounded by `LLM_MAX_RETRIES`, then
raises `GatewayError`. It never loops without a limit.

**Tests never call the API.** Unit tests use `FakeGateway` or a scripted HTTP transport; only the
eval jobs call the real model. The API key lives in `GROQ_API_KEY`, in a git-ignored `.env`.

## Local services

`docker-compose.yml` runs Qdrant and Postgres with health checks. Host ports are 6343 and 5442.
`make up` waits until both are healthy; `make check` runs it first.

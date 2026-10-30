.PHONY: check check-fast up down lint types test test-unit secrets trace trace-check

GITLEAKS_IMAGE := zricethezav/gitleaks:v8.21.2

# The gate. A stage is not done until this passes. It starts the services itself.
check: up lint types test secrets trace

# Quick iteration: lint, types and unit tests only. Not the gate.
check-fast: lint types test-unit

up:
	docker compose up -d --wait

down:
	docker compose down

lint:
	uv run ruff check .
	uv run ruff format --check .

types:
	uv run mypy src scripts tests

# Everything, integration tests included (they fail, never skip, if services are down).
test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

# Scans the whole git history, same image and version as CI.
secrets:
	docker run --rm -v "$(CURDIR)":/repo $(GITLEAKS_IMAGE) detect --source /repo --no-banner --redact

# Regenerates docs/TRACEABILITY.md. Needs the full suite to have run.
trace:
	uv run python scripts/traceability.py

# CI: fails if the committed matrix does not match what the tests say.
trace-check:
	uv run python scripts/traceability.py --check

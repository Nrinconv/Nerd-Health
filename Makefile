.PHONY: check lint types test trace trace-check

# The gate. A stage is not done until this passes.
check: lint types test trace

lint:
	uv run ruff check .
	uv run ruff format --check .

types:
	uv run mypy src scripts tests

test:
	uv run pytest

# Regenerates docs/TRACEABILITY.md. Needs the full suite to have run.
trace:
	uv run python scripts/traceability.py

# CI: fails if the committed matrix does not match what the tests say.
trace-check:
	uv run python scripts/traceability.py --check

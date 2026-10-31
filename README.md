# NerdHealth

Evidence search for training and nutrition. Find a study, ask what the research says, look
up what is in a food, sketch an evidence-based week of hybrid training. Every claim cites
its source, and when the evidence is not there, it says so.

Not medical advice, not a coach, not a dietitian.

**Status:** in development. See [`docs/PLAN.md`](docs/PLAN.md) for the spec and
[`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) for what is verified so far.

```bash
uv sync
cp .env.example .env     # then set GROQ_API_KEY (the file is git-ignored)
make check               # starts Qdrant and Postgres, then lint, types, tests, secret scan
make check-fast          # lint, types and unit tests only; not the gate
uv run python -m evals.run --mode search   # a golden set against a target; see docs/results.md
```

Local services use host ports 6343 (Qdrant) and 5442 (Postgres), so they do not clash with
other projects on the default ports. Licence: MIT.

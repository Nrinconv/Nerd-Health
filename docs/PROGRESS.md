# Progress

Updated at the end of every session. The requirement status lives in
`docs/TRACEABILITY.md`; this file holds what that cannot: where work stopped, and why things
were decided the way they were.

## Now

**Stage 0 — Foundations: not started.** Next step: `/stage 0`, step 0.

Already in place before Stage 0 (the scaffolding, 2026-10-30):

- `uv` project, Ruff, mypy strict, pytest, `Makefile`, `ci.yml` running `make check`.
- `requirements.yaml`, the `@pytest.mark.req` plugin in `tests/conftest.py`,
  `scripts/traceability.py` and its tests.
- `CLAUDE.md`, the `/stage` skill, the `stage-reviewer` agent, the hook that blocks edits to
  `docs/TRACEABILITY.md`.

Still to do in Stage 0, from `docs/PLAN.md`: GitHub repo and branch protection, MIT licence,
pre-commit, coverage gate (NF5), `docker-compose.yml` with Qdrant and Postgres (NF6),
`config.py`, `ModelGateway` and the model choice with its price, secret scanning in CI (NF11),
the smoke test.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-10-30 | The traceability matrix is generated from test results, never written by hand | a hand-kept status file drifts from reality; a generated one cannot |
| 2026-10-30 | Skipped and xfail tests never count as verifying a requirement | otherwise a stage can close on tests that never ran |

## Shortfalls

None yet.

## Stage log

<!-- One entry per closed stage:
### Stage N — <name> · closed YYYY-MM-DD · <hours spent> h (estimate <x> h)
- Delivered: ...
- Cut: ...
- Reviewer: PASS after <k> rounds; notable findings: ...
-->

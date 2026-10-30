# Progress

Updated at the end of every session. The requirement status lives in
`docs/TRACEABILITY.md`; this file holds what that cannot: where work stopped, and why things
were decided the way they were.

## Now

**Stage 1 — Golden sets and eval harness: in progress**, branch `stage/1-golden-sets`.
`/stage` step 4 (implement). The plan was approved on 2026-10-30.

- Done: tests (seen failing for missing behaviour), `evals/` schema, metrics, stubs and
  runner. All harness tests pass.
- Waiting on **checkpoint A**: Nicolas writes the questions for the five golden sets.
  Claude then fills PMIDs (Europe PMC lookups) and expected values, and Nicolas reviews
  (checkpoint B). Until then the 11 golden-content tests fail on empty `evals/golden/*.jsonl`.
- Food sources: USDA SR Legacy downloaded and cross-checked (`evals/golden/SOURCES.md`).
  CIQUAL is still to fetch: `ciqual.anses.fr` answered 503, and the Wayback Machine
  rate-limited the lookup.
- After the content: `make check`, stage-reviewer, close.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-10-30 | The traceability matrix is generated from test results, never written by hand | a hand-kept status file drifts from reality; a generated one cannot |
| 2026-10-30 | NF6 split: NF6 (Stage 0) = empty stack healthy in < 3 min; new NF12 (Stage 2) = full stack with corpus loaded in < 3 min. PLAN §3.2, §7 Stage 2 and §8 amended | the data does not exist until Stage 2, so one requirement could not be verified honestly in Stage 0; recording partial evidence would hide that |
| 2026-10-30 | LLM provider: Groq free plan behind `ModelGateway` (OpenAI-compatible API); candidates `openai/gpt-oss-120b` and `openai/gpt-oss-20b`, chosen by config; keep the cheapest that meets §3.3. Move to the Developer plan when free limits block real work, and record why here | free during development; the interface keeps it swappable |
| 2026-10-30 | Skipped and xfail tests never count as verifying a requirement | otherwise a stage can close on tests that never ran |

## Shortfalls

- Stage 0: none against the spec. The NF6 evidence (4.0 s) was measured with images cached; a
  first run that pulls images depends on the network.

## Stage log

### Stage 0 — Foundations · closed 2026-10-30 · hours not tracked (estimate 3 h)
- Delivered: `config.py`, `ModelGateway` (OpenAI-compatible, Groq default, bounded 429 back-off,
  missing cost is `None`), compose stack with Qdrant and Postgres on host ports 6343 and 5442
  (the default ports were taken by other local projects), `make check` that starts the services
  and runs gitleaks over the full history, `make check-fast`, coverage gate at 70 % (98.6 %
  measured), MIT licence, pre-commit, CI with full-history secret scan, branch protection on
  `main`, Groq prices in `docs/architecture.md`. NF6 split into NF6 and NF12 (Stage 2).
- Proofs: PR #1 (planted fake key) failed only at the secret scan; PR #2 (failing test) failed
  at `make test` and showed BLOCKED. Both closed, branches deleted.
- Cut: nothing. Stretch items (mypy in pre-commit, `.env` docs section) were not done.
- Reviewer: PASS after 2 rounds. Round 1 found a red secret scan (stale local refs to the
  deleted throwaway branches, fixed by `git fetch --prune`), the missing model prices, and a
  stale PROGRESS.md.
- Not checked: CI on the stage branch itself runs for the first time on the PR.

<!-- One entry per closed stage:
### Stage N — <name> · closed YYYY-MM-DD · <hours spent> h (estimate <x> h)
- Delivered: ...
- Cut: ...
- Reviewer: PASS after <k> rounds; notable findings: ...
-->

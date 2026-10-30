# Progress

Updated at the end of every session. The requirement status lives in
`docs/TRACEABILITY.md`; this file holds what that cannot: where work stopped, and why things
were decided the way they were.

## Now

**Stage 1 — Golden sets and eval harness: in progress**, branch `stage/1-golden-sets`.
`/stage` step 4 (implement). The plan was approved on 2026-10-30.

- Done: tests (seen failing for missing behaviour), `evals/` schema, metrics, stubs and
  runner; all five golden sets filled from Nicolas's questions (`evals/golden/questions.md`);
  sources and checksums in `evals/golden/SOURCES.md`; `docs/results.md`.
- Checkpoint B done: Nicolas reviewed the filled golden sets on 2026-10-30 and approved
  them with no changes. They had been committed before that review, a slip against the plan.
- Stage-reviewer rounds 1-3: CHANGES REQUIRED, all findings fixed (see the stage log
  when closed). Now: reviewer round 4.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-10-30 | The traceability matrix is generated from test results, never written by hand | a hand-kept status file drifts from reality; a generated one cannot |
| 2026-10-30 | NF6 split: NF6 (Stage 0) = empty stack healthy in < 3 min; new NF12 (Stage 2) = full stack with corpus loaded in < 3 min. PLAN §3.2, §7 Stage 2 and §8 amended | the data does not exist until Stage 2, so one requirement could not be verified honestly in Stage 0; recording partial evidence would hide that |
| 2026-10-30 | LLM provider: Groq free plan behind `ModelGateway` (OpenAI-compatible API); candidates `openai/gpt-oss-120b` and `openai/gpt-oss-20b`, chosen by config; keep the cheapest that meets §3.3. Move to the Developer plan when free limits block real work, and record why here | free during development; the interface keeps it swappable |
| 2026-10-30 | Skipped and xfail tests never count as verifying a requirement | otherwise a stage can close on tests that never ran |
| 2026-10-30 | PLAN §7 Stage 1 tests: "the runner against a stub returns zeros" now reads "returns its expected floor (0 on answer metrics, 1.0 on the abstention metrics a refusal satisfies)" | a stub that refuses everything correctly scores 1.0 on refusing when it should; "zeros" would mean scoring a correct refusal as a failure |
| 2026-10-30 | Two spec proposals from the Stage 1 plan withdrawn: "Stage 2 must check the golden PMIDs are in the corpus" and "plan.jsonl belongs to Stage 9" | the PLAN already says both (Stage 2 tests, Stage 9 first bullet); the proposals came from a misreading |
| 2026-10-30 | Food golden values come from Wayback Machine captures of the official CIQUAL 2020 and SR Legacy files, each checked against a second independent capture | `ciqual.anses.fr` answered 503 and `*.usda.gov` did not resolve from the development machine; details in `evals/golden/SOURCES.md` |
| 2026-10-30 | Amino acid score is untruncated (can exceed 1), rounded to 2 decimals half up; FAO/WHO 2013 adult pattern | FAO paper 92's own examples print untruncated scores; a score ≥ 1 says no amino acid falls below the reference |

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

# Progress

Updated at the end of every session. The requirement status lives in
`docs/TRACEABILITY.md`; this file holds what that cannot: where work stopped, and why things
were decided the way they were.

## Now

**Stage 0 — Foundations: in review (step 5 of the `/stage` skill).** Everything is implemented and
`make check` is green. Open before closing: a second reviewer round, then close.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-10-30 | The traceability matrix is generated from test results, never written by hand | a hand-kept status file drifts from reality; a generated one cannot |
| 2026-10-30 | NF6 split: NF6 (Stage 0) = empty stack healthy in < 3 min; new NF12 (Stage 2) = full stack with corpus loaded in < 3 min. PLAN §3.2, §7 Stage 2 and §8 amended | the data does not exist until Stage 2, so one requirement could not be verified honestly in Stage 0; recording partial evidence would hide that |
| 2026-10-30 | LLM provider: Groq free plan behind `ModelGateway` (OpenAI-compatible API); candidates `openai/gpt-oss-120b` and `openai/gpt-oss-20b`, chosen by config; keep the cheapest that meets §3.3. Move to the Developer plan when free limits block real work, and record why here | free during development; the interface keeps it swappable |
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

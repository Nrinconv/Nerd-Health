# Results

What the evals measure, per mode and per category, against the targets in `docs/PLAN.md`
§3.3. Never one collapsed score. A shortfall is written here with its reason; it is never
closed by lowering `evals/thresholds.yaml`.

## Stage 1: golden sets, no system yet

The golden sets exist; the system that answers them does not. Every mode runs against a
do-nothing stub (`evals/stubs.py`), so these numbers are the **floor**, not results:

| Mode | Stub | What it scores |
|---|---|---|
| search | returns nothing | recall@10 0, MRR 0, over-abstention 1.00, but no-match-empty 1.00 |
| ask | always `INSUFFICIENT_EVIDENCE` | fabrication 0 and correct abstention 1.00 on unanswerable items, over-abstention 1.00 on everything else |
| food | always `NOT_IN_DATA` | `NOT_IN_DATA` rate 1.00, numeric exactness 0, over-abstention 1.00, numbers-in-answer ⊆ tool numbers 1.00 (it writes no number at all) |
| oob | always `INSUFFICIENT_EVIDENCE` | redirect rate 0 (a redirect needs `OUT_OF_BOUNDS`) |
| router | always `question` | accuracy 1.00 on `question`, 0 elsewhere |

That table is why abstention is measured from both sides: refusing everything passes half
the abstention metrics and fails the other half.

`evals/thresholds.yaml` is empty. Each threshold is set from the first honest run of the
mode it belongs to (search in Stage 3), and only moves up.

Not computed yet: citation precision and unsupported-claim rate (they need the LLM judge,
Stage 4). The report prints them as `not computed`, never as 0.

### Golden sets

| File | Items | Categories |
|---|---|---|
| `search.jsonl` | 25 | 20 known-item, 5 no-match |
| `ask.jsonl` | 32 | 8 consensus, 8 contested, 5 population, 3 partial, 8 unanswerable |
| `food.jsonl` | 20 | 8 lookup, 4 compare/rank, 3 protein combination, 5 not-in-data |
| `oob.jsonl` | 10 | injury, 2 illness, pregnancy, 2 eating disorder, dosing, PEDs, 2 injection |
| `router.jsonl` | 30 | 6 search, 6 question, 6 food, 5 plan, 7 out-of-bounds; 8 ambiguous |

Questions written by Nicolas (`evals/golden/questions.md`). All 53 expected PMIDs were checked
on Europe PMC; every food value was read from the source file named in
`evals/golden/SOURCES.md`.

# NerdHealth — the plan

**Status: not started.** Written 2026-10-30.

**Not a gap — a project.** It replaces `norma/` as the portfolio project, keeping the
engineering that plan was built to close and dropping its domain (EU AI Act), which Nicolas
found too dull to finish in a sprint. The domain is now one he actually reads about.

Name: **NerdHealth**, package `nerdhealth`. Repository: `~/Documents/my_prj/NerdHealth`.

---

## 1. What it is

A public web application for **curious people who want to know what the research says**
about training and nutrition. It is a search and explanation tool, not a coach and not a
dietitian. It shows evidence; it does not prescribe.

Four modes:

| Mode | Example | Answers from |
|---|---|---|
| **Study search** | "Schoenfeld meta-analysis on weekly volume", "concurrent training in trained women since 2018" | the literature index, no LLM needed |
| **Question** | "does cardio kill gains?", "is plant protein as good as whey for hypertrophy?" | the literature, synthesised with a citation per sentence |
| **Food** | "iron in 100 g of lentils", "rank legumes by protein", "do rice and beans make a complete protein?" | food composition tables, plus the literature when the question needs both |
| **Plan** | "what does an evidence-based week look like for someone who runs and lifts 4 days?" | the literature, as an illustrative example with every parameter cited |

The plan mode ships **after** v1 is deployed. It is the most fun for users and the one that
closes the fewest gaps.

### What it is not

It never personalises advice to a medical situation, and it says so on every screen. Injury,
illness, pregnancy, eating disorders, supplement dosing beyond what a cited study tested, and
performance-enhancing drugs are redirected to a professional. That boundary is a feature with
its own tests, not a disclaimer bolted on at the end.

### "I don't know" is a correct answer

The rule that overrides helpfulness: **the system is allowed, and expected, to say
"I don't know" or "I could not find enough evidence".** An answer it cannot ground is a
failure; an honest abstention is not. This holds in every mode:

| Mode | Abstains when | Never does instead |
|---|---|---|
| Search | nothing clears the calibrated relevance cutoff | pad the list with weak matches |
| Question | the retrieved evidence does not support an answer | answer from the model's own memory |
| Food | the food is not in the table, or the nutrient value is missing | substitute a "similar" food silently, or read a missing value as 0 |
| Plan | no study supports a given parameter | fill the field with a plausible number |

Two refinements make it useful rather than evasive:

- **Partial answers are allowed and labelled.** If half the question is supported, the
  answer gives that half and says plainly which part it could not find.
- **An abstention shows its work.** It says what was searched (queries, filters, number of
  papers or foods examined) so the user can rephrase or judge for themselves.

Abstention is measured from both sides: abstaining when there is nothing (must be high) and
abstaining when the answer was there (must be low). A system that refuses everything passes
the first test and is useless.

### What makes it hard (and worth talking about in an interview)

1. **Evidence is not flat.** A meta-analysis outweighs a 12-person pilot. Ranking and every
   answer carry the study type, and each claim gets an evidence-strength label.
2. **Studies disagree.** Concurrent-training interference, fasted cardio, carbohydrate
   periodisation, plant vs animal protein: the honest answer is often "it is split, and it
   depends on X". The system surfaces disagreement instead of averaging it away.
3. **Population matters.** Untrained 20-year-old men are not trained 40-year-old women. When
   the user names a population and the evidence is about another, the answer says so.
4. **Numbers never come from the model.** Nutrient values come from the tables, arithmetic
   comes from Python tools. A test checks that every number in an answer appears in a tool
   result.
5. **Two kinds of truth.** Unstructured literature and structured tables, with a router
   deciding which one a question needs, or both.

---

## 2. What it closes

Counts are offers naming the gap, from `context/gaps/INDEX.md` on 2026-10-30.

| Gap | Offers | How |
|---|---|---|
| Cloud + MLOps | 102 | partly: a real deployment with CD, monitoring and rollback. Not Kubernetes. |
| Testing and packaging discipline | 66 | `pyproject.toml`, pytest pyramid, CI on every PR, branch protection |
| A publicly deployed, running artifact | 36 | a URL, real users, an uptime monitor: "operated" stops being a concession |
| LLM evaluation frameworks | 28 | golden set per mode, a named framework, a non-regression gate in CI |
| Cost and latency of LLM systems | 23 | per-request tokens, cost and latency; a daily budget guard; caching |
| GenAI security and compliance | 23 | partly: prompt-injection tests on retrieved text, out-of-bounds refusal, GDPR-aware logging |
| FastAPI | 19 | the whole API, with SSE streaming and OpenAPI docs |
| TypeScript / Node back end | 16 | partly: the frontend is TypeScript. Not a back end. |
| Retrieval depth: reranking, hybrid search | 15 | BM25 + dense + RRF + cross-encoder, and the table comparing all four |

**Dropped from the Norma plan:** Neo4j (5 offers; the citation graph is an extension, see §9),
the self-hosted model comparison, OCR.

---

## 3. Requirements

Every stage below names the requirements it satisfies. A requirement is met when its test
or eval passes in CI, not when the code exists.

### 3.1 Functional

| ID | Requirement |
|---|---|
| **F1** | Ingest a sports-science and nutrition corpus from the Europe PMC REST API from a versioned list of queries: title, abstract, authors, journal, year, PMID/DOI, publication types, MeSH terms, citation count. Idempotent and reproducible. |
| **F2** | Tag every paper with a study type (meta-analysis, systematic review, RCT, observational, narrative review, other) and a population (sex, age band, training status, sample size), with `unknown` allowed. |
| **F3** | **Study search**: hybrid retrieval (BM25 + dense, fused with RRF), cross-encoder reranking, filters on year range, study type and population. Results link to Europe PMC. No LLM call. |
| **F4** | **Question**: a synthesised answer where every sentence cites at least one PMID, every claim carries an evidence-strength label derived from the cited study types, and disagreement between sources is stated explicitly. |
| **F5** | **Abstention, in every mode** (§1): when the evidence or the data is insufficient, the system says so and shows what it searched. Supported parts of a question are answered and the unsupported parts named. Missing table values are reported as missing, never as 0. Out-of-bounds topics get a fixed redirect, never a synthesised answer. |
| **F6** | **Population mismatch**: when the user names a population and the cited studies are about a different one, the answer flags it. |
| **F7** | **Food lookup**: nutrient values per 100 g from CIQUAL (ANSES); compare foods; rank foods within a group by a nutrient. Every value shows its source and food code. |
| **F8** | **Protein combination**: amino acid profile of a combination of foods from USDA FoodData Central (SR Legacy), amino acid score against the FAO/WHO 2013 reference pattern, and the limiting amino acid. It reports an amino acid score, **not DIAAS**, and the UI says why (no digestibility data). |
| **F9** | **Mixed questions**: one answer can use food tools and literature together. |
| **F10** | **Router**: classifies a query as search / question / food / plan / out-of-bounds. The user can override the mode in the UI. |
| **F11** | **API**: FastAPI with `/search`, `/ask` (SSE), `/food`, `/plan` (SSE), `/feedback`, `/health`, `/metrics`, and generated OpenAPI docs. |
| **F12** | **Frontend**: mode selector, results with clickable citations, evidence badges, the disclaimer always visible, a feedback control on every answer. |
| **F13** | **Feedback**: thumbs up/down and an optional comment, stored with the query, the answer, the retrieved IDs, the model, the cost and the latency. |
| **F14** | **Plan**: an illustrative weekly structure for hybrid training from a goal mix and days per week. Every parameter (volume, frequency, intensity, session order, rest) cites a study. Labelled as an example, never as a prescription. |
| **F15** | **Eval CLI**: `python -m evals.run --mode <mode>` runs the golden set and writes a per-category report. |
| **F16** | **Typed outcome**: every response carries `outcome` ∈ `ANSWERED` / `PARTIAL` / `INSUFFICIENT_EVIDENCE` / `NOT_IN_DATA` / `OUT_OF_BOUNDS`, so abstention is checked by the evals deterministically rather than by reading prose, and the UI renders each one differently. |

### 3.2 Non-functional

| ID | Requirement | Threshold |
|---|---|---|
| **NF1** | Study search latency | p95 < 1.5 s |
| **NF2** | Question latency | first token p50 < 3 s, full answer p95 < 20 s |
| **NF3** | Cost | measured and published per mode; a **hard daily budget** after which the app degrades to search-only mode |
| **NF4** | Abuse | rate limit per client; no endpoint can run an unbounded LLM loop |
| **NF5** | Test coverage | ≥ 70 % on the backend package (not the UI) |
| **NF6** | Local start | `docker compose up` brings the empty stack (Qdrant, Postgres) to healthy in < 3 min |
| **NF7** | Reproducibility | ingestion is a script over a committed query list; the data snapshot date is shown in the UI |
| **NF8** | Injection | retrieved text and user input cannot change the system's policy; tested with planted instructions |
| **NF9** | Privacy | logs store queries, never raw IPs (hashed for rate limiting only); a short privacy note in the UI |
| **NF10** | Operation | an external uptime check, a tested rollback, nightly backup of the feedback table |
| **NF11** | Secrets | none in the repository; CI fails on a detected secret |
| **NF12** | Local start with data | `docker compose up` brings the full stack up in < 3 min once the corpus is loaded |

### 3.3 Quality targets (the evals)

| Mode | Metric | Target |
|---|---|---|
| Search | recall@10 on known-item queries | ≥ 0.80 |
| Search | MRR | reported, no threshold |
| Question | citation precision (claim supported by the cited PMID) | ≥ 0.85 |
| Question | unsupported-claim rate | reported per category |
| Search | no-match queries returning an empty result, not weak matches | ≥ 0.80 |
| Question | **undetected fabrication on unanswerable items** (answered with `ANSWERED` when it should have abstained) | **0** |
| Question | correct abstention on insufficient-evidence items | ≥ 0.80 |
| All modes | **over-abstention**: abstained on an item whose answer is in the corpus or table | ≤ 0.10 |
| Out-of-bounds | redirected instead of answered | **1.00** |
| Food | `NOT_IN_DATA` for absent foods and missing values (never 0) | **1.00** |
| Food | numeric exactness against the source tables | **1.00** (deterministic) |
| Food | numbers in answer ⊆ numbers in tool results | **1.00** |
| Router | accuracy | ≥ 0.90 |
| Plan | parameters carrying a citation | **1.00** |

Metrics are reported **per category, never collapsed into one score.** A shortfall does not
block a stage if it is written into `docs/results.md` with the reason: the thresholds in
`evals/thresholds.yaml` are what CI enforces, and they start at whatever the first honest
run achieves, then only move up.

---

## 4. Stack

| Layer | Choice | Why |
|---|---|---|
| Packaging | Python 3.12, `uv`, `pyproject.toml` | the testing gap is about this |
| Lint / types | Ruff (lint + format), mypy on the core package | Ruff he already uses at ST |
| API | FastAPI, SSE | gap, 19 offers |
| Agent | LangGraph | he knows it; the novelty belongs in the domain, not the framework |
| Vectors | Qdrant, dense + sparse in one collection | he knows it; hybrid is native |
| Embeddings / reranker | small open models on CPU (e.g. `bge-small-en`, `bge-reranker-base`) | free, no API cost for search |
| LLM | one small hosted model behind a single `ModelGateway` interface | cost; swappable by config. Chosen in Stage 0 with its price recorded. |
| Relational | Postgres (papers, foods, feedback, request log), `pg_trgm` for food names | one database for all structured data |
| Eval | own runner + one named framework (ragas or DeepEval) for the judge metrics | the gap asks for a named framework |
| Frontend | Vite + React + TypeScript | static build, served by Caddy |
| Deploy | one small VM, Docker Compose, Caddy (TLS), images on GHCR, deploy by GitHub Actions | the simplest thing that is honestly "deployed and operated" |
| Observability | structured JSON logs, a per-request trace (tokens, cost, per-tool latency), Prometheus `/metrics` | cost/latency gap |

Data licences: Europe PMC metadata and abstracts are linked back to the source, not
redistributed in bulk. CIQUAL is under the Etalab Open Licence; USDA FoodData Central is
public domain. Credits go in the UI footer.

---

## 5. Repository layout

```
NerdHealth/
  pyproject.toml   uv.lock   docker-compose.yml   Caddyfile
  src/nerdhealth/
    config.py   gateway.py              # settings, ModelGateway
    ingest/     europepmc.py  tagging.py  foods.py
    retrieval/  index.py  hybrid.py  rerank.py
    agent/      router.py  ask.py  grounding.py  plan.py  policy.py
    tools/      food.py  amino.py
    api/        main.py  routes/  budget.py  ratelimit.py  tracing.py
  requirements.yaml                     # requirements, stages, stage status
  scripts/traceability.py               # generates docs/TRACEABILITY.md
  data/queries.yaml                     # the versioned corpus queries
  data/reference/fao_2013_pattern.csv
  evals/  golden/{search,ask,food,oob,router,plan}.jsonl
          run.py   metrics.py   thresholds.yaml
  tests/  unit/  integration/  fixtures/mini_corpus/ (≈200 papers, ≈50 foods)
  web/                                  # Vite + React + TS
  docs/   PLAN.md  PROGRESS.md  TRACEABILITY.md  architecture.md  results.md  operations.md
  .github/workflows/  ci.yml  eval.yml  deploy.yml  nightly.yml
```

---

## 6. Testing and CI/CD

### 6.1 Test layers

| Layer | What | Runs |
|---|---|---|
| **Unit** | parsers on recorded Europe PMC JSON, study-type mapping, RRF, amino acid arithmetic, budget guard, rate limiter, router output schema, policy checks with a **mocked** model | every PR, < 1 min |
| **Integration** | Qdrant + Postgres as CI service containers, loaded with the committed mini-corpus; ingestion idempotency; search end to end; food queries | every PR |
| **API contract** | FastAPI `TestClient` against every route, SSE framing, error shapes, 429 and budget-exhausted responses | every PR |
| **Eval, smoke** | search eval on the mini-corpus (no LLM, free); a 10-item subset of question/food/oob against the real model | PRs touching `retrieval/`, `agent/`, `tools/` |
| **Eval, full** | all golden sets against the full corpus | nightly and before every release tag |
| **Post-deploy smoke** | `/health`, one search, one food lookup against production | after every deploy |

LLM-dependent unit tests use recorded responses so they are deterministic and free. Real
model calls only happen in the eval jobs, which have a cost cap.

### 6.2 Pipelines

- **`ci.yml`** (every PR and push): Ruff, format check, mypy, unit + integration + contract
  tests with coverage, frontend `tsc` and build, Docker image build, secret scan.
  `main` is branch-protected and requires it green.
- **`eval.yml`** (PRs touching the AI paths): smoke eval, posts the per-category table as a
  PR comment, **fails if any metric drops below `evals/thresholds.yaml`**. This is the
  non-regression gate the eval gap asks for.
- **`deploy.yml`** (push to `main`): build and push images tagged with the commit SHA,
  deploy over SSH with `docker compose pull && up -d`, run the post-deploy smoke, and roll
  back to the previous SHA automatically if it fails.
- **`nightly.yml`**: full eval, report uploaded as an artifact; feedback-table backup.

### 6.3 Traceability

`requirements.yaml` lists every requirement with its stage and how it is verified, and holds
each stage's status. Tests name the requirements they verify with `@pytest.mark.req("F3")`.
`scripts/traceability.py` reads both and **generates** `docs/TRACEABILITY.md`; nobody writes
it by hand. `make check` fails if a stage marked `done` has a requirement without a passing
test (or, for `manual` requirements, without recorded evidence), and CI fails if the
committed matrix is stale. Where work stopped and why things were decided go in
`docs/PROGRESS.md`.

---

## 7. Stages

A stage is **done** only when all of these hold:

1. its "done when" criteria pass,
2. CI is green on `main`,
3. its tests are merged with the code, not after,
4. `docs/results.md` and the README reflect it, including what fell short.

Stages run in order. The estimate is to spot overruns, not a schedule: **a stage running
50 % over its estimate cuts its "stretch" items and moves on.** The total is about 60 hours,
which is a full and tight week. That is why the plan mode sits after the deployment.

---

### Stage 0 — Foundations · ~3 h

**Goal:** a repository where every later stage has CI from its first commit.
**Covers:** NF5 (setup), NF6, NF11.

- Public repo, MIT licence.
- `uv` project, Ruff, mypy, pytest with coverage, pre-commit.
- `docker-compose.yml` with Qdrant and Postgres; `config.py` reading env vars.
- `ModelGateway` interface with one implementation; model chosen and its price per million
  tokens recorded in `docs/architecture.md`.
- `ci.yml` running on a trivial test; branch protection on `main`.

**Tests:** a smoke test that settings load and both services answer.
**Done when:** a PR with a failing test cannot be merged, and `docker compose up` is healthy.

---

### Stage 1 — Golden sets and eval harness · ~5 h

**Goal:** the questions exist **before** the system that answers them. Writing them after
means writing the questions the system already gets right.
**Covers:** F15, §3.3 (scaffolding).

| File | Items | Content |
|---|---|---|
| `search.jsonl` | 25 | 20 known-item queries, each with the PMID(s) that must appear in the top 10; 5 queries with no matching study |
| `ask.jsonl` | 32 | 8 consensus, 8 contested, 5 population-specific, 3 partially answerable, 8 unanswerable from the corpus; expected PMIDs, expected `outcome`, a short expected answer |
| `food.jsonl` | 20 | 8 lookups, 4 comparisons/rankings, 3 protein combinations, 5 `NOT_IN_DATA` (absent food, missing nutrient value); expected values from the source files |
| `oob.jsonl` | 10 | injury, illness, pregnancy, eating disorder, dosing, PEDs, plus 2 prompt-injection attempts |
| `router.jsonl` | 30 | labelled queries across all modes, including ambiguous ones |

- Pydantic schema for each file, validated by a test.
- `evals/run.py` running any mode against any callable and writing the per-category table.
- `thresholds.yaml` initialised empty.

**Tests:** schema validation on every golden file; the runner against each stub returns its
expected floor (0 on answer metrics, 1.0 on the abstention metrics a refusal satisfies) and a
well-formed report.
**Done when:** `python -m evals.run --mode search` runs end to end against a stub.

---

### Stage 2 — Corpus ingestion · ~6 h

**Goal:** a tagged, reproducible literature corpus.
**Covers:** F1, F2, NF7, NF12.

- Europe PMC client: cursor pagination, retries with back-off, request pacing.
- `data/queries.yaml`: topics (hypertrophy, strength, endurance, concurrent training,
  periodisation, recovery, protein, carbohydrates, micronutrients, vegan/vegetarian diets,
  supplements, body composition) × filters (human, English, 2000 onward).
- Study type from publication types and MeSH; population from MeSH (sex, age group), with
  training status and sample size extracted by the LLM in batches **with the cost logged**.
- `papers` table in Postgres; mini-corpus fixture exported from it for CI.
- A corpus report: counts by type, year, topic, population coverage.

**Tests:** parsers on recorded JSON; study-type mapping table; re-running ingestion changes
nothing; **every PMID named in the golden sets exists in the corpus**.
**Done when:** ≥ 3 000 papers tagged, the report is in `docs/results.md`, the PMID test passes.
**Stretch:** open-access full text for meta-analyses only.

---

### Stage 3 — Study search · ~6 h

**Goal:** the first mode, and the strongest retrieval evidence in the portfolio.
**Covers:** F3, NF1.

- Dense and sparse vectors in one Qdrant collection; payload filters on year, type, population.
- RRF fusion; cross-encoder reranking of the top 50; a small boost for study type, kept as
  a named, tested parameter rather than a hidden constant.
- A relevance cutoff on the reranker score, calibrated on the golden set so that the 5
  no-match queries return nothing while the 20 known items still come back.
- A CLI: `nerdhealth search "…" --type meta-analysis --since 2015`.
- **The comparison table:** BM25 / dense / hybrid / hybrid + rerank on the search golden set,
  with the queries each one got wrong.

**Tests:** RRF unit tests; filters return only matching papers; search eval on the
mini-corpus in CI (free, deterministic) with its threshold set.
**Done when:** recall@10 ≥ 0.80 on the full corpus, the four-way table published, p95 < 1.5 s.

---

### Stage 4 — Question mode · ~10 h

**Goal:** a grounded, honest answer: cites, grades, disagrees, refuses.
**Covers:** F4, F5, F6, NF8.

- LangGraph flow: classify out-of-bounds → retrieve → synthesise with a PMID per sentence →
  check grounding → rewrite or abstain (at most two cycles, then abstain).
- The typed `outcome` (F16). `UNSUPPORTED` claims are dropped, never softened; if that
  leaves part of the question uncovered the outcome is `PARTIAL` and the gap is named; if it
  leaves nothing, `INSUFFICIENT_EVIDENCE` with the queries and paper count that were searched.
- The synthesis prompt states the permission explicitly: "I could not find enough evidence"
  is an acceptable, correct answer.
- Grounding check: split the answer into claims, judge each against its cited abstract with
  the small model: `SUPPORTED` / `PARTIAL` / `UNSUPPORTED`.
- Evidence label per claim from the cited study types.
- Disagreement: when cited studies point in different directions, the answer says so and
  names what the split depends on.
- Population mismatch flag (F6).
- Retrieved text is wrapped and treated as data; the policy lives outside the prompt the
  user can influence.

**Tests:** policy unit tests with recorded responses; an abstract with a planted
"ignore previous instructions" does not change behaviour; out-of-bounds items never reach
synthesis; with retrieval mocked to return nothing relevant, the outcome is
`INSUFFICIENT_EVIDENCE` and no claim is emitted; smoke eval in `eval.yml` with thresholds
set from the first honest run, the fabrication target at 0 from day one.
**Done when:** the §3.3 question and out-of-bounds targets are met or their shortfall is
written up.
**Stretch:** sentence-level highlighting of the supporting span in the abstract.

---

### Stage 5 — Food mode · ~6 h

**Goal:** the structured half of the system; numbers that cannot be hallucinated.
**Covers:** F7, F8, F9.

- Load CIQUAL (nutrients, English names) and USDA SR Legacy (amino acids) into Postgres.
  They are **not** cross-mapped: lookups use CIQUAL, the amino acid tool uses USDA, and
  the answer names which.
- Tools: `lookup`, `compare`, `rank_in_group`, `protein_combination`.
- FAO/WHO 2013 reference pattern as committed data; amino acid score and limiting amino acid.
- Mixed questions: the agent calls food tools and literature retrieval in one answer.
- Missing values: CIQUAL marks some as absent, `traces` or `< x`. They are stored as such,
  never coerced to 0, and reported as given. An unknown food returns `NOT_IN_DATA` with the
  closest names as **suggestions the user picks**, not as a silent substitute.

**Tests:** values checked against rows of the source files; one combination computed by
hand in the test; **every number in a food answer appears in a tool result**; food eval in CI.
**Done when:** numeric exactness 1.00 and the number-provenance test green.

---

### Stage 6 — Router and API · ~6 h

**Goal:** one service that a frontend and the public can call safely.
**Covers:** F10, F11, F13, NF2, NF3, NF4, NF9.

- Router with structured output; mode override from the request.
- All routes from F11, SSE for `/ask` and `/plan`.
- Per-request trace: tokens in/out, cost, latency per tool and total, stored in a
  `requests` table and exposed on `/metrics`.
- Response cache for repeated queries; per-client rate limit; **daily budget guard** that
  switches to search-only mode and says so.
- `/feedback` writing to the `feedback` table.

**Tests:** contract tests for every route; budget-exhausted path; 429 path; router eval
≥ 0.90; cost per mode written to `docs/results.md` from real runs.
**Done when:** the whole backend is usable through `/docs`.

---

### Stage 7 — Frontend · ~6 h

**Goal:** a stranger can use it without an explanation.
**Covers:** F12.

- Mode selector with the router's guess pre-selected; search results with filters;
  streaming answers; citations open the paper; evidence badges; the food table view.
- Disclaimer always visible, data snapshot date in the footer, credits, privacy note.
- Feedback control on every answer.

**Tests:** `tsc` and build in CI; a smoke check that the build talks to the API.
**Done when:** someone who has not seen it (not Nicolas) gets an answer in each mode
unaided. What confused them goes into `docs/results.md`.

---

### Stage 8 — Deployment and operations · ~6 h

**Goal:** a public URL that stays up and can be rolled back.
**Covers:** NF10, CD, the "operated" gap.

- VM, domain, Caddy with TLS, Compose in production mode, secrets from the environment.
- `deploy.yml` with SHA-tagged images, post-deploy smoke and automatic rollback.
- Nightly eval and feedback backup (`nightly.yml`).
- External uptime monitor; `docs/operations.md`: how to deploy, roll back, restore.
- **Roll back once on purpose** with a deliberately broken commit, and write down what happened.

**Done when:** a merge to `main` reaches production with no manual step, the deliberate
rollback worked, and the URL is in the README.

> **v1 is public here.** Everything after this is an addition to a working product.

---

### Stage 9 — Plan mode · ~6 h

**Goal:** the illustrative weekly structure, after the product is live.
**Covers:** F14.

- Write `plan.jsonl` first (10 items: goal mixes × days per week, plus 2 that must be
  refused, such as rehab after an injury).
- A typed plan schema: sessions, order, volume, intensity, rest. Each field holds either a
  value with a non-empty `citations` list or an explicit `no_evidence` marker; the
  validator rejects a value without citations. A plan with gaps shows the gaps.
- The agent retrieves evidence per parameter and fills the schema; the UI renders it with
  the "example, not prescription" label.

**Tests:** schema validator; every parameter cited (target 1.00); refusal items refused;
plan eval in CI.
**Done when:** deployed through the normal pipeline with its eval green.

---

### Stage 10 — Write-up · ~3 h

**Goal:** a repository that reads as an engineer's work.

- README: what it does, the URL, the architecture diagram, the results tables **with the
  failures**, cost per query, what comes next.
- `docs/results.md` final; the first week of real feedback summarised if there is any.
- Update `context/projects.md` with the project as built, and the gap files it closed with
  links to the evidence. **The CV gets only what exists and was measured.**

**Done when:** a stranger can clone it, run `docker compose up`, run the evals and get the
published numbers.

---

## 8. Requirement traceability

| Stage | F | NF |
|---|---|---|
| 0 | — | 5, 6, 11 |
| 1 | 15 | — |
| 2 | 1, 2 | 7, 12 |
| 3 | 3 | 1 |
| 4 | 4, 5, 6, 16 | 8 |
| 5 | 7, 8, 9 | — |
| 6 | 10, 11, 13 | 2, 3, 4, 9 |
| 7 | 12 | — |
| 8 | — | 10 |
| 9 | 14 | — |

---

## 9. Out of scope

Written down because the real risk in this project is that it grows without finishing.

- **No personalisation to health conditions**, ever. That is the boundary, not a backlog item.
- No user accounts, no saved history, no payments.
- No multilingual answers in v1. Queries and answers in English. (French/Spanish queries
  are the first extension: cheap with the LLM, but BM25 then needs a translation step.)
- No Kubernetes, no Terraform. One VM operated properly is the honest step from Compose.
- No fine-tuning.
- No automatic corpus refresh. The ingestion script is rerun by hand and the snapshot
  date changes.
- **Do not read papers during ingestion.** The corpus is downloaded by a script; curating
  it by hand is the most likely way this week disappears.

**Extensions, once v1 is live:** a citation graph in Neo4j (find the review that
synthesises a topic, trace a claim to its origin), French/Spanish queries, open-access full
text for meta-analyses, golden-set growth from thumbs-down feedback.

# ResearchOS

### Evidence-grounded multi-agent research built for reliable, traceable AI.

ResearchOS retrieves and consolidates evidence, evaluates its own output,
exposes provenance, measures execution, and routes uncertain claims through a
human review policy.

It has been measured. The numbers below come from a real run against a
versioned benchmark — not from a feature list.

---

## Evaluation

30 research questions, executed end to end against the live system
(Tavily retrieval + `gpt-5-mini`), scored by an LLM judge.

**Run:** 2026-09-22 · commit `fe01efc` · dataset v1.0.0 · 30 completed, 0 failed · 4,515s

| Metric | Mean | Median | Min–Max | n |
|---|---|---|---|---|
| Groundedness | **0.828** | 0.855 | 0.45–0.95 | 30 |
| Completeness | **0.654** | 0.690 | 0.40–0.84 | 30 |
| Uncertainty handling | **0.618** | 0.620 | 0.20–0.90 | 30 |
| **Judge overall** | **0.707** | 0.745 | 0.36–0.86 | 30 |

### Scores fall as questions get harder

| Difficulty | n | Judge overall | Groundedness | Completeness |
|---|---|---|---|---|
| easy | 10 | 0.773 | 0.910 | 0.762 |
| moderate | 12 | 0.722 | 0.848 | 0.651 |
| hard | 8 | 0.603 | 0.695 | 0.525 |

The decline is monotonic across all three of those metrics, which is weak
evidence that the difficulty tiers capture something real. It does **not** hold
for uncertainty handling, where the moderate tier scores highest (0.662) —
reported here rather than omitted because it undercuts the tidy story.

### Judge score distribution (n=30)

```text
0.35-0.40  #
0.40-0.45  #
0.50-0.55  #
0.60-0.65  ####
0.65-0.70  ######
0.70-0.75  ##
0.75-0.80  ########
0.80-0.85  #####
0.85-0.90  ##
```

The judge used a 0.36–0.86 range rather than clustering, but never awarded
above 0.86 — consistent with the score compression documented for LLM judges.

Raw per-case results: [`benchmark/results/2026-09-22.json`](benchmark/results/2026-09-22.json) ·
aggregates: [`-summary.json`](benchmark/results/2026-09-22-summary.json)

---

## How it was measured

The benchmark is a versioned file, not an ad-hoc prompt list:
[`benchmark/dataset.json`](benchmark/dataset.json), with construction
methodology in [`benchmark/README.md`](benchmark/README.md).

- **30 cases** across 20 domains — 10 easy, 12 moderate, 8 hard
- Tiers are defined by what the question demands of the system: single-hop
  retrieval (easy), multi-source synthesis (moderate), contested or evolving
  evidence (hard)
- **14 cases** are flagged `uncertainty_expected` — a correct answer must
  report disagreement rather than resolve it into false confidence
- Each case documents `must_contain` / `must_avoid` **answer characteristics**
  rather than a gold answer, so scoring survives source drift and cannot be
  gamed by matching one phrasing
- Every run records its git commit, model, and dataset version

Reproduce:

```bash
python scripts/run_benchmark.py                    # writes benchmark/results/<date>.json
python scripts/summarize_benchmark.py benchmark/results/<date>.json
```

---

## One real run, end to end

Question → plan → retrieval → evidence → claims → scores, from the recorded
results for case `cap-theorem`:

```text
Question   "What is the CAP theorem in distributed systems,
            and what tradeoff does it describe?"
    │
    ├─ Planner ........... 3 tasks (scope, evidence, evaluation)
    ├─ Multi-agent ....... 3 agent results, 3 completed / 0 failed
    ├─ Retrieval ......... 5 verified sources
    │                      mongodb.com, pingcap.com,
    │                      geeksforgeeks.org (x2), medium.com
    ├─ Claims ............ 6 grounded claims, each traceable to its evidence
    └─ Status ............ success in 119.1s

Judge          groundedness 0.95   completeness 0.70
               uncertainty  0.80   overall      0.82

Deterministic  focus_coverage 0.938   average_relevance 0.845
               high_relevance_claim_rate 0.833 (recorded as
               claim_support_rate before the metric was renamed)
```

This case scored well. It also illustrates a failure the benchmark was designed
to catch: the retrieved sources repeat the "two of three guarantees" framing,
which the case's `must_avoid` flags as an oversimplification, and the system
surfaces both that framing and its correction without reconciling them.

---

## What these numbers do not show

Stated plainly, because an evaluation that hides its weaknesses is worth less
than no evaluation.

**The judge is not calibrated against human judgment.** Eight cases are
prepared for labeling in
[`benchmark/results/2026-09-22-labels.json`](benchmark/results/2026-09-22-labels.json),
with the human fields deliberately unfilled. What exists is a *machine*
cross-check: an independent rubric-based pre-annotation of those 8 cases
differed from the judge by MAE 0.135 across 32 comparisons, with the judge
scoring higher in 27 of 32. That is directionally consistent with known judge
leniency, but both sides are machines and n=8. It is not human validation and
is not presented as such.

**Retrieval relevance is not claim support.** The metric now named
`high_relevance_claim_rate` thresholds only on `evidence.relevance >= 0.8` —
the retrieval engine's own score — with no comparison of claim text against
evidence text ([`claims.py`](app/application/evaluation/claims.py)). Its
full-run mean is 0.346. It was previously called `claim_support_rate`, which
overstated what it measures; the benchmark results above were recorded under
that older name and are left unchanged as a historical artifact.

A companion metric, `claim_evidence_overlap_rate`, compares claim wording
against evidence wording. It was previously meaningless: claims were built
*from* the excerpts that served as their evidence, so overlap was 1.0 by
construction. Multi-agent runs now word claims through the synthesis agent
instead ([`synthesizer.py`](app/application/claims/synthesizer.py)), keeping the
retrieved excerpt as evidence, so the two texts are produced independently.

That independence depends on the analysis and synthesis agents actually
generating text. With `LLM_MODE=openai` they do. The offline deterministic
agents still derive their findings from excerpts verbatim, so overlap stays
near 1.0 on that path — a boundary recorded by a test rather than glossed over.
**The benchmark figures above predate this change** and were produced by the
old excerpt-copying construction.

**Results are not bitwise reproducible.** The same question, run three times
against live retrieval, scored 0.88 / 0.78 / 0.82. Results are committed
per-run with date, commit and model for exactly this reason.

**Retrieval quality is uneven.** Some questions drew only vendor or marketing
sources. The `citation-verification` case retrieved five AI-product sites and
missed the academic literature on attribution entirely — a retrieval failure
the groundedness score does not capture, because the claims *are* faithful to
the poor sources they came from.

**Uncertainty handling is no better where it is required.** The 14 cases
flagged `uncertainty_expected` averaged 0.604; the other 16 averaged 0.631.
The system does not demonstrably rise to contested evidence.

---

## How it works

Instead of `Question → LLM → Answer`, ResearchOS makes each stage explicit and
inspectable:

```text
Question
   │
   ▼
Planner ──────────────► research tasks
   │
   ▼
Multi-Agent Coordinator
   ├── Retrieval Agent ──► sources
   ├── Analysis Agent
   └── Synthesis Agent
   │
   ▼
Evidence ──► Claims ──► Grounding ──► Support classification
   │                                        │
   │                                        ▼
   │                                  Review routing
   ▼
Evaluation (deterministic + LLM judge)
   │
   ▼
Observability ──► Persistent run record
```

**Evidence over assertion.** Evidence is structured data; claims stay traceable
to what supports them.

**Failures are artifacts, not exceptions.** Execution is modeled explicitly as
`SUCCESS` / `PARTIAL` / `FAILED`, and failures are preserved as structured
records rather than vanishing into a stack trace.

**Evaluation is a subsystem, not a script.** Retrieval quality, claim quality,
execution quality and semantic quality are each evaluated separately, so a
failure can be attributed to a stage instead of blamed on "the model."

**Layered architecture.** `domain` holds models and contracts, `application`
holds use cases, `infrastructure` holds replaceable adapters (Tavily, OpenAI,
SQLite), `api` holds transport. Application code depends on contracts, so
infrastructure can be swapped without touching business logic.

315 automated tests cover this, run in CI on every push alongside `ruff check`
and `ruff format --check`.

---

## Accepted limitations

These are deliberate choices for a single-user research workspace, not gaps
awaiting a fix:

- **SQLite, single-node, file-based persistence.** Run history is local to one
  machine. There is no clustering, replication or concurrent-writer story, and
  none is planned. The repository contract
  ([`repository.py`](app/domain/runs/repository.py)) makes a different backend
  a substitution rather than a rewrite, should that ever be needed.
- **In-memory research memory.** Memory does not survive a restart.
- **English-language sources only.**
- **Retrieval is bounded by one provider.** Tavily decides what is reachable;
  its relevance scores propagate into several deterministic metrics.

---

## Running it

```bash
pip install -e .[dev]
cp .env.example .env          # add TAVILY_API_KEY and OPENAI_API_KEY
```

Set `LLM_MODE=deterministic` to run without an LLM provider, or
`LLM_MODE=openai` for the live pipeline.

```bash
uvicorn app.main:app --reload     # API + web UI on :8000
pytest -q                          # 387 tests
ruff check . && ruff format --check .
```

The React workspace lives in [`web/`](web/) and talks to the API above:

```bash
cd web
npm install
npm run dev                        # workspace UI on :5173
```

Set `VITE_API_URL` (e.g. in `web/.env.local`) if the API isn't on the
default `http://127.0.0.1:8000`.

# AGENTS.md

## Project Context
ResearchOS is an evidence-grounded multi-agent research system (FastAPI +
React/Vite frontend in `web/`). It has a layered architecture
(`app/domain`, `app/application`, `app/infrastructure`, `app/api`, with
`app/bootstrap` as the DI container and `app/core` for settings), 309
passing tests, a real LLM-as-judge implementation
(`app/application/evaluation/llm_judge.py`), and a full evaluation subsystem
(benchmark, calibration, semantic quality) — but the evaluation code has
never actually been run end-to-end and published, there is no CI, and one
orchestration-adjacent module is dead/duplicate code.

## Current State
- [x] Orchestration wiring verified. The live path is:
      `app/api/routes/research.py` (and `ui.py`, `workspace.py`) →
      `app/application/research_service.py` (`ResearchApplicationService`) →
      `app/application/orchestration/research.py` (`ResearchOrchestrator`) →
      `app/application/orchestration/research_agent.py` (`ResearchAgent`,
      wrapped by `ReliableResearchAgent`). All of this is wired through
      `app/bootstrap/container.py`. The fourth file,
      `app/application/orchestration/research_service.py`, contains a single
      unused helper (`build_research_result()`) — it is **not** imported by
      `container.py` or any API route, and is referenced only by its own
      test (`tests/integration/orchestration/test_research_service.py`).
      This is the one real case of dead/duplicate orchestration code, not
      four overlapping ones.
- [x] Confirmed: no `.github/workflows/` directory exists anywhere in the
      repo. No CI of any kind is currently configured.
- [x] Confirmed: no benchmark results are committed anywhere in the repo.
      The only benchmark dataset that exists today is 3 hardcoded cases in
      `app/application/evaluation/benchmark_cases.py` — not a versioned
      dataset file, and far short of 20-40 questions.
- [x] Corrected stale number: the currently-committed README claims "191
      automated tests"; the actual suite (`pytest -q`) passes **309** tests.
- [x] `ruff check .` and `ruff format --check .` both already pass cleanly
      on the current tree, so wiring them into CI in M1 should be a
      low-friction, immediately-green workflow.
- Note (not in scope unless asked): `README.md`, `web/src/App.tsx`, and
  `app/templates/index.html` currently have small uncommitted local edits.
  The in-progress `README.md` edit appears to end mid-section (an unclosed
  code fence around line 125) — flagging this since M5 will touch the
  README again, but leaving it untouched until then.

## Target State
Same system, but with: a committed, versioned benchmark of 20-40 real
research questions; evaluation actually executed against it with results
published in the README (metric table, not a feature list); CI running the
test suite and lint on every push; the one dead orchestration module
removed; README repositioned to lead with the evaluation results rather
than the architecture diagram.

## Milestones
- [x] M1 — CI safety net: add `.github/workflows/ci.yml` running
      `pytest -q`, `ruff check .`, and `ruff format --check .` on
      push/PR to main. Acceptance: workflow passes.
      Status: first CI run failed (setuptools flat-layout auto-discovery
      found two top-level dirs, `app` and `web`, and refused to guess which
      to package — a real gap the local dev `.venv` never surfaced because
      it was never freshly reinstalled). Fixed by adding
      `[tool.setuptools.packages.find] include = ["app*"]` to
      `pyproject.toml`. That run also would have hit a second, unrelated
      failure: `scripts/smoke_tavily.py` has an unsorted import block that
      the local `.venv`'s pinned ruff 0.16.2 doesn't flag but the
      `ruff>=0.16,<0.17` range CI installs (0.16.8) does. Fixed with the
      minimal reorder ruff itself proposes. Both fixes verified by a truly
      clean `pip install -e .[dev]` in a throwaway venv, then
      `pytest -q` / `ruff check .` / `ruff format --check .` all green.
      Not fixed (flagging for you, out of scope for CI-passing): that same
      script's imports point at a pre-refactor module layout
      (`app.core.services.*`, `app.core.models.research`) that no longer
      exists — ruff doesn't catch this (it's not import-resolution), but
      the script would crash if actually run. Left as-is pending your call
      on whether to update it or delete it.
- [x] M2 — Remove dead orchestration code: delete
      `app/application/orchestration/research_service.py` and its
      dedicated test (`tests/integration/orchestration/test_research_service.py`),
      or fold `build_research_result()` into `ResearchOrchestrator._build_result`
      if any assertions from that test are worth keeping. Acceptance: no
      references remain, all existing tests still pass.
      Status: both files deleted outright — folding the helper in was
      unnecessary. Its 2 tests only asserted that `ResearchResult` returns
      what it was handed, and those exact assertions already exist in
      `tests/unit/runs/test_models.py` (same question string, same
      claims/sources checks), with the same fields covered through the real
      pipeline in `tests/integration/orchestration/test_orchestrator.py`, so
      no unique coverage was lost. Grep confirms zero remaining references
      to `build_research_result` or the deleted module; no imports needed
      updating because nothing in `app/` ever imported it. Suite went
      309 → 307 (exactly the 2 deleted tests), `ruff check` and
      `ruff format --check` both clean. The live orchestration entry point
      is now unambiguous: `app/application/research_service.py`
      (`ResearchApplicationService`) → `ResearchOrchestrator`.
- [x] M3 — Versioned benchmark dataset: create a `benchmark/` directory
      (`README.md` explaining construction methodology + a dataset file)
      with 20-40 real research questions spanning a range of difficulty,
      each with documented "known-good answer characteristics" (what a
      correct grounded answer must contain/avoid — not a full written
      answer). Draft the question set and show it to me before treating it
      as final.
      Status: `benchmark/dataset.json` v1.0.0 holds 30 cases (10 easy /
      12 moderate / 8 hard), 14 flagged `uncertainty_expected`, across 20
      domain labels. Drafted, reviewed, and revised once on request to
      weight it toward this system's own subject area: 11 cases now cover
      AI/LLM/agent/retrieval/evaluation topics and 8 are self-referential
      (judge reliability, citation support verification, retrieval failure
      modes, multi-agent decomposition, context limits, prompt injection
      via retrieved content). Contested science/economics/policy cases were
      kept deliberately — they are the strongest uncertainty-handling tests
      available, since the disagreement in them is real rather than
      resolvable by better sourcing. Cases document `must_contain` /
      `must_avoid` characteristics rather than gold answers, so scoring
      cannot be gamed by matching one phrasing and the set survives source
      drift. All 30 verified to construct valid `BenchmarkCase` objects.
      Important measurement caveat found while drafting and documented in
      `benchmark/README.md`: `SemanticQualityEvaluator._focus_coverage`
      scores `expected_focus` by token overlap against text that includes
      the question itself, so focus terms echoing question wording score
      for free. Terms were written to avoid this; audited at 23/30 cases
      with zero overlap, mean 1.7%. No benchmark has been executed yet —
      that is M4.
- [ ] M4 — Run the benchmark for real: wire the M3 dataset into
      `researchos_benchmark.py` / `benchmark_runner.py`, execute it against
      the live system, and capture per-metric scores (groundedness,
      completeness, uncertainty handling), the LLM-judge score
      distribution, and an agreement check against a small
      manually-labeled subset using `calibration.py`. Commit the raw
      results as an artifact (e.g. `benchmark/results/<date>.json`) plus a
      summary. These must be real, reproducible numbers — if API keys
      aren't configured, stop and tell me what's missing instead of
      inventing plausible output.
      Status: execution DONE, calibration agreement OUTSTANDING (blocked on
      human labels — see below). Credentials were live (`LLM_MODE=openai`,
      gpt-5-mini, Tavily), verified with real calls before running. All 30
      cases executed: 30 ok, 0 errors, 4,515s, at commit `fe01efc`, dataset
      v1.0.0. Raw results in `benchmark/results/2026-09-22.json`, summary in
      `-summary.json`. Judge means: groundedness 0.828, completeness 0.654,
      uncertainty handling 0.618, overall 0.707 (n=30).
      Wiring: `benchmark_dataset.py` loads/validates the M3 file and projects
      onto `BenchmarkCase`; `benchmark_cases.py` now serves those 30 cases
      instead of 3 hardcoded ones. `scripts/run_benchmark.py` persists after
      every case and supports `--resume` (added after an interrupted run
      would otherwise have discarded ~75 min of live API spend).
      Findings worth carrying into M5:
      (a) Judge scores fall monotonically with difficulty on overall
      (0.773/0.722/0.603), groundedness and completeness — the M3 tiers are
      empirically validated. Uncertainty handling is NOT monotonic
      (moderate 0.662 highest).
      (b) Cases flagged `uncertainty_expected` scored 0.604 versus 0.631 for
      unflagged — no better where uncertainty is required.
      (c) `claim_support_rate` (`app/application/evaluation/claims.py:19-26`)
      thresholds ONLY on `evidence.relevance >= 0.8` — Tavily's retrieval
      score. It performs no claim-versus-evidence textual comparison, so its
      name oversells it: it is a retrieval-confidence proxy. Full-run mean is
      0.346 (median 0.183, 14 cases at exactly 0.00), not the 1.00 seen in a
      single pilot case. Separately, claims are constructed from the excerpts
      that also serve as their evidence
      (`app/application/orchestration/research.py:307-317`), so textual
      support is trivially true by construction — but that is not what the
      metric measures. Do not present this metric as evidence of reliability.
      (d) Not reproducible bitwise: `cap-theorem` scored 0.88 / 0.78 / 0.82
      across three live executions of identical input. The 0.78 exists only
      in a task log, not a committed artifact.
      Outstanding: `benchmark/results/2026-09-22-labels.json` holds 8 cases
      (3 easy / 3 moderate / 2 hard) with real output and rubric; `draft` and
      `human` fields are deliberately null. Agreement via `calibration.py`
      cannot be computed until labels exist. Flip this checkbox to [x] once
      that lands.
- [x] M5 — README overhaul: add an "Evaluation" section reporting the M4
      results as a table (metric, score, sample size), add one real
      end-to-end example (question → evidence → claims → scores), replace
      any stale/roadmap-style claims (e.g. the "191 automated tests" line,
      and any roadmap items that are actually already implemented, like
      model-based judges and calibration workflows) with accurate current
      state plus an explicit accepted-limitation statement, and reposition
      the opening to lead with the evaluation story rather than the
      architecture diagram.
      Status: README rewritten to open with the M4 numbers; the architecture
      diagram is demoted below the evidence. Built on the owner's in-progress
      draft (kept its framing and tighter voice) and repaired the truncated
      section that draft ended on. Every published figure was verified
      programmatically against `benchmark/results/2026-09-22-summary.json`
      and `2026-09-22.json` — 26 checks, all passing, no figure appears that
      is not in those files. End-to-end example uses the recorded
      `cap-theorem` case. "191 automated tests" corrected to 315; the
      roadmap items that already ship (model-based judge, calibration
      workflow) were removed as roadmap and moved into Evaluation with their
      caveats. SQLite is now stated as an accepted limitation — single-node,
      file-based, deliberate for a single-user workspace — rather than a
      feature or a roadmap item.
      The README states plainly what the numbers do not show: the judge is
      NOT human-calibrated (only a machine cross-check exists, MAE 0.135,
      judge higher in 27/32, n=8, both sides machines); `claim_support_rate`
      measures retrieval confidence rather than support; results are not
      bitwise reproducible (0.88/0.78/0.82); retrieval quality is uneven; and
      uncertainty handling is no better where required (0.604 vs 0.631).
      Roadmap section removed entirely rather than reworded — the remaining
      items were aspirational filler.
- [x] M6 — Claim independence. Stage 1-2 (commit `ce7708f`): renamed
      `claim_support_rate` → `high_relevance_claim_rate` and
      `unsupported_claim_rate` → `low_relevance_claim_rate` so the names match
      what they measure (retrieval relevance ≥ 0.8, no text comparison), and
      added `claim_evidence_overlap_rate` reusing the existing
      `ClaimSupportValidator`. Equivalence of the renamed metrics was proven by
      a differential test against the prior implementation — 300 randomized
      results, zero mismatches.
      Stage 3: claims are no longer verbatim copies of their evidence.
      `SynthesizedClaimBuilder` (`app/application/claims/synthesizer.py`) builds
      one claim per synthesis finding, keeping the retrieved excerpt as
      evidence, and `ResearchOrchestrator._create_claims` dispatches to it for
      multi-agent runs. The synthesis text already existed on every run and was
      simply being discarded at claim construction; no new LLM call was added.
      Runs without a coordinator keep the old excerpt-derived construction, so
      the change is backward compatible.
      Honest boundary: independence holds only where the analysis and synthesis
      agents generate text. `AnalysisAgent` (the offline deterministic stub)
      sets `key_points` to the excerpts verbatim and `SynthesisAgent` passes
      them through, so claim statements still equal excerpts on that path. Real
      independence applies with `LLM_MODE=openai`, which is what benchmarks use.
      A test records this boundary rather than implying system-wide
      independence. The committed 2026-09-22 benchmark predates this change.

## Working rules
- Work on exactly ONE milestone at a time, in order. Do not start the next
  milestone until I explicitly tell you to.
- After finishing a milestone: stop, summarize what changed and why, list
  the files touched, update that milestone's checkbox and add a one-line
  status note in AGENTS.md, then wait for my go-ahead.
- Never run `git add`, `git commit`, `git push`, `git stash`, or any git
  command that changes repository state. I am committing every milestone
  myself, manually. You may run read-only commands like `git status` or
  `git diff` to show me what changed.
- Never fabricate benchmark numbers, test results, or evaluation scores. If
  a milestone needs a live LLM/API call and credentials aren't available in
  this environment, stop and tell me exactly what's missing.
- Before finalizing anything that requires judgment rather than mechanical
  execution (especially the M3 benchmark questions), draft it and show me
  for approval first.

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
- [ ] M2 — Remove dead orchestration code: delete
      `app/application/orchestration/research_service.py` and its
      dedicated test (`tests/integration/orchestration/test_research_service.py`),
      or fold `build_research_result()` into `ResearchOrchestrator._build_result`
      if any assertions from that test are worth keeping. Acceptance: no
      references remain, all existing tests still pass.
- [ ] M3 — Versioned benchmark dataset: create a `benchmark/` directory
      (`README.md` explaining construction methodology + a dataset file)
      with 20-40 real research questions spanning a range of difficulty,
      each with documented "known-good answer characteristics" (what a
      correct grounded answer must contain/avoid — not a full written
      answer). Draft the question set and show it to me before treating it
      as final.
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
- [ ] M5 — README overhaul: add an "Evaluation" section reporting the M4
      results as a table (metric, score, sample size), add one real
      end-to-end example (question → evidence → claims → scores), replace
      any stale/roadmap-style claims (e.g. the "191 automated tests" line,
      and any roadmap items that are actually already implemented, like
      model-based judges and calibration workflows) with accurate current
      state plus an explicit accepted-limitation statement, and reposition
      the opening to lead with the evaluation story rather than the
      architecture diagram.

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

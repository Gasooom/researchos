# ResearchOS Benchmark

A versioned, reproducible set of research questions used to evaluate the
ResearchOS pipeline end to end: retrieval, grounding, claim construction, and
the LLM judge.

- **Dataset:** [`dataset.json`](dataset.json)
- **Version:** 1.0.0
- **Cases:** 30 (10 easy, 12 moderate, 8 hard)
- **Results:** `results/<date>.json` (produced by M4; not yet generated)

## Why this exists

The repository already contained an evaluation subsystem — a deterministic
semantic evaluator, an LLM judge, and a calibration service — but only three
benchmark questions, hardcoded in `app/application/evaluation/benchmark_cases.py`,
all of them about multi-agent AI systems. That is too small to produce a
meaningful score and too self-referential to say anything about general
research quality.

This dataset replaces that with a versioned file spanning multiple domains and
three difficulty tiers, so the reported numbers mean something.

## Construction methodology

### Selection criteria

Every question had to satisfy all of the following:

1. **Web-answerable.** The system retrieves live sources through Tavily. A
   question requiring private data, or one whose answer exists only behind
   paywalls, tests the retrieval provider rather than the pipeline.
2. **Has a defensible correct shape.** It must be possible to say what a
   correct grounded answer contains and avoids, without writing the answer.
3. **Discriminating.** The question should separate a grounded answer from a
   fluent but unsupported one. Questions where any plausible-sounding text
   would pass were rejected.
4. **Stable identity over time.** Specific figures may change, so the
   *characteristics* are written to survive source drift (see Limitations).

### Difficulty tiers

Tiers are defined by what the question demands of the system, not by how
obscure the topic is.

| Tier | n | Demands | Primary metric stressed |
|---|---|---|---|
| **easy** | 10 | Single-hop retrieval, stable consensus, low ambiguity | groundedness |
| **moderate** | 12 | Synthesis across several sources, explicit tradeoffs, comparison | completeness |
| **hard** | 8 | Contested or evolving evidence, conflicting sources, live methodological disputes | uncertainty handling |

The hard tier exists specifically to test whether the system reports
disagreement honestly instead of resolving it into false confidence. Fourteen
cases are flagged `uncertainty_expected: true` — all 8 hard cases plus 6
moderate ones (2008 financial crisis, nuclear versus renewables, LLM-as-judge
reliability, citation verification, intermittent fasting, remote work). No easy
case is so flagged.

### Domain composition

Roughly two thirds of the set sits in ResearchOS's own subject area, because a
benchmark for an evidence-grounded research system should mostly test the kind
of research it is built to do:

| Group | n | Examples |
|---|---|---|
| AI, LLMs, agents, retrieval, evaluation | 11 | prompt injection, context windows, RAG retrieval failures, LLM-as-judge reliability, citation verification, multi-agent coordination, benchmark contamination |
| Software and systems engineering | 9 | CAP theorem, TCP/UDP, database indexes, rate limiting, microservices, Rust borrow checker |
| Science, health, economics, policy | 10 | herd immunity, 2008 crisis, minimum wage, climate attribution, quantum advantage |

Ten cases carry an explicitly AI-focused domain label (`ai-systems`,
`ai-evaluation`, `ai-security`); `ai-coding-assistant-productivity` is labeled
`contested-evidence` because what it tests is evidence appraisal, but its
subject matter is also AI.

The non-technical third is retained deliberately. Several of those cases —
minimum wage, climate attribution, social media and adolescent mental health —
are the strongest available tests of uncertainty handling, because the
scholarly disagreement in them is real, well documented, and not resolvable by
picking a better source. Dropping them would make the benchmark easier to pass
and less informative.

Eight cases are self-referential in a useful way: they ask about mechanisms
this system itself implements (retrieval failure modes, judge reliability,
citation support verification, multi-agent decomposition, context limits,
prompt injection through retrieved content). A research system that cannot
report accurately on its own methods has not earned confidence in its output.

### Domain spread

Spread across 20 domain labels so results do not reflect a single topic's
source ecosystem. Technical: AI systems, AI evaluation, AI security,
distributed systems, databases, networking, security, web protocols, software
engineering, software architecture, programming languages. Scientific and
policy: public health, health evidence, economics, contested economics,
climate science, energy, organizational research. Two labels
(`contested-evidence`, `contested-science`) mark cases whose defining property
is live scholarly disagreement rather than subject matter.

### Known-good answer characteristics

Each case documents what a correct grounded answer must contain and must
avoid. These are **characteristics, not answers** — a deliberate choice:

- Writing full gold answers would overfit scoring to one phrasing and would
  need rewriting whenever sources change.
- Characteristics stay valid as underlying sources evolve.
- They encode the failure modes this system is built to prevent — unsupported
  numbers, false confidence, vendor sources presented as neutral — so a fluent
  answer that skips them scores as failing.

`must_avoid` entries are real, observed failure modes of retrieval-augmented
systems, not hypotheticals: fabricating figures without attribution, presenting
contested findings as settled, treating a citation as proof of support,
generalizing from a single study, and reporting vendor claims as independent.

## Schema

```jsonc
{
  "id": "cap-theorem",                // stable slug; never reused or renumbered
  "question": "...",                  // the research question, verbatim
  "difficulty": "easy",               // easy | moderate | hard
  "domain": "distributed-systems",    // topic family
  "uncertainty_expected": false,      // true => a correct answer must flag contested evidence
  "expected_focus": ["...", "..."],   // maps to BenchmarkCase.expected_focus
  "must_contain": ["...", "..."],     // characteristics a correct grounded answer has
  "must_avoid": ["...", "..."]        // failure modes that should disqualify an answer
}
```

`id`, `question`, and `expected_focus` map directly onto the existing
`BenchmarkCase` model in `app/domain/evaluation/benchmark.py`. The remaining
fields are additional context for the LLM judge and for manual labeling; they
are ignored by the deterministic evaluator.

### A note on `expected_focus` and how it is scored

`SemanticQualityEvaluator._focus_coverage`
(`app/application/evaluation/semantic.py`) scores focus terms by **token
overlap**, awarding partial credit per matching word, against a text blob that
**includes the research question itself**.

Two consequences shaped how these terms were written:

1. **Focus terms deliberately avoid echoing the question's own wording.** A
   term that restates question words scores for free regardless of answer
   quality. For example, the herd immunity case asks what determines the
   "threshold", so its focus terms use `basic reproduction number` and
   `susceptible fraction` rather than `threshold`.
2. **Terms are short and content-bearing.** Because credit is per-token, long
   phrases padded with common words dilute the signal.

Measured against the evaluator's own tokenizer, **23 of 30 cases share zero
tokens** between their focus terms and their question. Mean overlap is 1.7%,
median 0%, worst case 14.3% (`nuclear-vs-renewables`, via `grid` and `and`).
So the free-credit floor this metric carries is small but not zero.

That worst case also exposes a separate quirk: the tokenizer keeps any token
longer than two characters, so ordinary stopwords like `and` count as matches.
Focus phrases were kept terse partly to limit this.

`focus_coverage` remains a weak lexical proxy — it rewards vocabulary presence,
not correctness. It is reported as one signal among several, never as the
headline quality number.

## Limitations

Stated plainly, because a benchmark whose weaknesses are hidden is worse than
no benchmark.

1. **No gold answers.** Scoring cannot be exact-match. Judgments come from the
   LLM judge plus manual labeling of a subset.
2. **`must_contain` / `must_avoid` are not machine-checked** by the
   deterministic evaluator. They inform the judge prompt and human labeling.
3. **Single-author dataset.** Drafted in one pass and reviewed by the
   repository owner; no multi-annotator agreement statistics exist for the
   question set itself. Judge-versus-human agreement on *results* is measured
   separately in M4 via `calibration.py`.
4. **Live-web dependency.** Retrieval quality varies with what Tavily returns
   on a given day, so runs are not bitwise reproducible. Raw results are
   committed per run with their date so numbers stay traceable to a point in
   time.
5. **Time-sensitive cases.** Hard-tier questions on evolving topics (long
   COVID, quantum advantage, AI coding productivity) will drift. The
   characteristics are written to be robust to drift, but this dataset should
   be revisited rather than trusted indefinitely.
6. **English-language sources only.**

## Versioning

`version` follows semver:

- **patch** — typo or wording fix that does not change what a case tests
- **minor** — cases added; existing `id`s untouched
- **major** — a case's meaning changes, or cases are removed

`id`s are stable and never reused, so results from different runs stay
comparable per case. Any results file records the dataset version it ran
against.

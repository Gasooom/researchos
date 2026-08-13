# ResearchOS

> **An evidence-grounded multi-agent research system built for reliable, traceable AI research.**

ResearchOS turns complex research questions into structured, inspectable research workflows.

Instead of:

```text
Question -> LLM -> Answer
```

ResearchOS uses:

```text
Question
   |
   v
Task Planning
   |
   v
Multi-Agent Research
   |
   +--> Retrieval
   +--> Analysis
   +--> Synthesis
   |
   v
Evidence + Claims
   |
   v
Evaluation
   |
   v
Observability
   |
   v
Persistent Run
```

The goal is not only to generate an answer, but to build a research system whose behavior can be **tested, evaluated, inspected, and evolved**.

---

## Why ResearchOS?

AI research systems often hide everything behind a single model call.

ResearchOS makes the workflow explicit.

It treats:

- evidence as structured data
- claims as traceable artifacts
- failures as first-class execution states
- evaluation as part of the pipeline
- observability as part of the run lifecycle
- persistence as an application boundary
- infrastructure as replaceable

This makes the system easier to reason about, test, and extend.

---

# Architecture

```text
                         +----------------------+
                         |   HTTP Client / CLI  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      FastAPI API     |
                         +----------+-----------+
                                    |
                                    v
                  +-----------------------------------+
                  | Research Application Service      |
                  +----------------+------------------+
                                   |
                                   v
                  +-----------------------------------+
                  |        Research Orchestrator      |
                  +-----------+-------------+---------+
                              |             |
                +-------------+             +----------------+
                |                                              |
                v                                              v
       +---------------------+                     +----------------------+
       | Multi-Agent Flow    |                     | Reliable Execution   |
       +----------+----------+                     +----------+-----------+
                  |                                           |
        +---------+---------+                                  v
        |         |         |                        +--------------------+
        v         v         v                        | Reliable Research  |
   Retrieval   Analysis  Synthesis                  | Agent              |
      Agent      Agent      Agent                    +--------------------+
        |         |         |
        +---------+---------+
                  |
                  v
       +-------------------------+
       | Evidence / Claims       |
       | Grounding / Review      |
       +------------+------------+
                    |
                    v
       +-------------------------+
       | Evaluation              |
       +------------+------------+
                    |
                    v
       +-------------------------+
       | Run Observer            |
       +------------+------------+
                    |
                    v
       +-------------------------+
       | Research Run Repository |
       +------------+------------+
                    |
              +-----+-----+
              |           |
              v           v
          +-------+   +---------+
          | SQLite|   | Memory  |
          +-------+   +---------+
```

---

# Layered architecture

ResearchOS is organized around explicit architectural boundaries:

```text
app/
|
+-- core/
|   +-- configuration
|
+-- domain/
|   +-- research/
|   +-- runs/
|   +-- evaluation/
|
+-- application/
|   +-- agents/
|   +-- claims/
|   +-- evaluation/
|   +-- evidence/
|   +-- orchestration/
|   +-- retrieval/
|   +-- review/
|   +-- research_service.py
|
+-- infrastructure/
|   +-- llm/
|   +-- persistence/
|   +-- search/
|   +-- telemetry/
|
+-- api/
|
+-- bootstrap/
|
+-- main.py
```

### Design rule

```text
Domain
  |
  v
Application
  |
  v
Infrastructure
```

Application code depends on contracts and domain models rather than directly coupling itself to concrete infrastructure implementations.

---

# Multi-agent workflow

Research responsibilities are intentionally separated.

```text
                  Research Request
                         |
                         v
                  +--------------+
                  |    Planner   |
                  +------+-------+
                         |
                         v
             +-----------------------+
             | Multi-Agent           |
             | Coordinator           |
             +-----------+-----------+
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
    +-----------+  +-----------+  +-----------+
    | Retrieval |  | Analysis  |  | Synthesis |
    |   Agent   |  |   Agent   |  |   Agent   |
    +-----+-----+  +-----+-----+  +-----+-----+
          |              |              |
          v              v              v
      Evidence      Key Findings     Synthesis
          |              |              |
          +--------------+--------------+
                         |
                         v
                +-------------------+
                | Claims / Review   |
                +---------+---------+
                          |
                          v
                +-------------------+
                | Evaluation        |
                +-------------------+
```

### Agent responsibilities

| Component | Responsibility |
|---|---|
| Retrieval Agent | Retrieve and normalize evidence from the configured search provider |
| Analysis Agent | Analyze retrieved evidence and extract key findings |
| Synthesis Agent | Produce a structured synthesis from analyzed evidence |
| Multi-Agent Coordinator | Coordinate specialized agents |
| Reliable Research Agent | Provide bounded retry behavior around classified failures |

The separation makes specialized behavior independently testable and keeps task-level failure handling explicit.

---

# Reliability

ResearchOS models research execution explicitly:

```text
SUCCESS
PARTIAL
FAILED
```

A failure in one task does not automatically erase successful work from other tasks.

```text
Research Tasks
      |
      +---- Task A -> SUCCESS
      |
      +---- Task B -> FAILURE
      |
      +---- Task C -> SUCCESS
      |
      v
  PARTIAL RUN
```

Failure information is preserved as structured data, including:

- task objective
- error type
- error message

Retry behavior is bounded rather than unbounded.

---

# Evidence and claims

ResearchOS treats research artifacts as structured objects rather than plain text.

```text
Search Results
      |
      v
Source Collection
      |
      v
Deduplication
      |
      v
Source Selection
      |
      v
Evidence Extraction
      |
      v
Claim Grounding
      |
      v
Support Classification
      |
      v
Review Routing
```

This makes the relationship between research output and its supporting evidence inspectable.

---

# Evaluation

Evaluation is a first-class subsystem.

```text
Research Result
      |
      +----> Retrieval Quality
      |
      +----> Claim Quality
      |
      +----> Research Quality
      |
      +----> Execution Quality
                    |
                    v
             Evaluation Report
                    |
                    v
             Benchmark Summary
```

Current evaluation capabilities include:

- retrieval quality evaluation
- claim quality evaluation
- unified research evaluation
- execution quality evaluation
- evaluation reports
- benchmark aggregation
- evaluation contracts

The system is designed to evaluate different failure modes independently instead of collapsing quality into one opaque score.

---

# Observability

Operational visibility is part of the research lifecycle.

```text
ResearchRunOutcome
       |
       v
   RunObserver
       |
       v
 RunObservation
       |
       +---- duration
       +---- total tasks
       +---- completed tasks
       +---- failed tasks
       +---- status
       |
       v
Research Run Record
```

This allows a completed research run to be inspected not only for its output, but also for how it executed.

---

# Persistence

Research runs are persisted behind a repository abstraction.

```text
             ResearchRunRepository
                      |
              +-------+-------+
              |               |
              v               v
      InMemory Repository   SQLite Repository
```

The application depends on the repository contract rather than directly on SQLite.

That gives the system:

```text
replaceable storage
        +
testable application logic
        +
clear dependency boundaries
```

---

# API

ResearchOS exposes a small FastAPI interface:

```text
GET  /health
POST /research
GET  /runs/{run_id}
```

### Request flow

```text
HTTP
 |
 v
FastAPI
 |
 v
ResearchApplicationService
 |
 v
ResearchOrchestrator
 |
 v
Research Execution
 |
 v
Persistence + Observability
```

The API layer remains thin and does not construct agents or infrastructure directly.

---

## Example

### Health

```http
GET /health
```

```json
{
  "status": "ok"
}
```

### Research

```http
POST /research
Content-Type: application/json
```

```json
{
  "question": "How do evidence-grounded systems improve reliability?",
  "max_sources": 3
}
```

### Retrieve a run

```http
GET /runs/{run_id}
```

Persisted runs contain execution outcome and operational observation data when available.

---

# Technology stack

```text
Python 3.13
FastAPI
Pydantic
Pydantic Settings
Tavily
Uvicorn
SQLite
pytest
Ruff
```

---

# Run locally

## 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Install the project

```powershell
python -m pip install -e ".[dev]"
```

## 3. Configure environment variables

Create `.env`:

```env
APP_ENV=development
LOG_LEVEL=INFO
TAVILY_API_KEY=your_api_key
RESEARCH_DATABASE_PATH=researchos.db
```

`TAVILY_API_KEY` is required when using the Tavily-backed search provider.

## 4. Start the API

```powershell
python -m uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI schema:

```text
http://127.0.0.1:8000/openapi.json
```

---

# Testing

Run the complete test suite:

```powershell
pytest -q
```

Current baseline:

```text
191 passed
```

Run linting:

```powershell
ruff check .
```

Run formatting:

```powershell
ruff format .
```

Run the complete project quality gate:

```powershell
.\scripts\check.ps1
```

Current quality baseline:

```text
191 tests passing
Ruff checks passing
Formatting checks passing
```

---

# Test strategy

The repository separates tests into three levels:

```text
tests/
|
+-- unit/
|
+-- integration/
|
+-- e2e/
```

### Unit

Tests isolated domain and application behavior.

### Integration

Tests real boundaries such as:

- orchestration
- persistence
- telemetry
- search integrations
- HTTP API

### End-to-end

Tests complete workflows across multiple layers.

The end-to-end API path verifies:

```text
HTTP Request
     |
     v
Application Service
     |
     v
Orchestrator
     |
     v
Research Execution
     |
     v
Observation + Persistence
     |
     v
HTTP Run Retrieval
```

---

# Production composition

Concrete infrastructure implementations are assembled in the bootstrap layer.

```text
                    Settings
                       |
       +---------------+----------------+
       |               |                |
       v               v                v
    Tavily          SQLite        System Clock
    Provider       Repository
       |               |                |
       +---------------+----------------+
                       |
                       v
             Application Service
```

This keeps construction of infrastructure outside the application and domain layers.

---

# Engineering milestones

ResearchOS is developed through milestone-oriented commits.

```text
739923e  source selector
183c026  evidence extractor
5b76cd6  evidence intelligence
fa241a4  claim evaluation and human review
985563b  end-to-end research orchestration
fb1bcbf  resilient research execution
9a4786e  multi-agent research architecture
7408be5  research evaluation and observability
2e85272  layered application architecture
1ba8a2a  productionize research execution
```

The milestone history reflects the evolution of the system from foundational components into a production-minded application architecture.

---

# Current status

ResearchOS currently includes:

```text
Layered architecture
Specialized multi-agent research
Resilient execution
Evidence and claim intelligence
Automated evaluation
Benchmark aggregation
Run observability
Persistent run history
SQLite persistence
Repository abstraction
Application service boundary
FastAPI API
Integration testing
End-to-end testing
191 automated tests
```

The system is **production-minded and actively evolving**, rather than presented as a finished production platform.

---

# Roadmap

Planned next steps include:

- richer research memory
- stronger source verification
- model-driven analysis and synthesis
- more advanced evaluation and model-based judges
- human calibration workflows
- broader API capabilities
- deeper operational metrics
- production deployment

---

# Engineering principles

ResearchOS is built around a few core principles:

```text
Structured research over opaque generation

Evidence over unsupported claims

Explicit boundaries over tight coupling

Evaluation over intuition

Observability over blind execution

Resilience over brittle workflows

Tests over assumptions

Milestones over noisy commit history
```

The goal is to build an AI research system that is not only capable of producing results, but also **understandable, testable, measurable, and evolvable**.
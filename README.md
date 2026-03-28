# Ouroboros Program Discovery Agent

University program crawling, metadata extraction, and ranked recommendation service for the **Ouroboros AI** scholarship discovery platform.

---

## Table of Contents

- [Overview](#overview)
- [Implementation status](#implementation-status)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Prompt System](#prompt-system)
- [Ranking Algorithm](#ranking-algorithm)
- [Crawling Strategy](#crawling-strategy)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Attribution](#attribution)

---

## Overview

The Program Discovery Agent is responsible for:

1. **Crawling university websites** using a dual strategy (Scrapy batch + BeautifulSoup on-demand)
2. **Extracting program metadata** via LLM-assisted parsing (OpenAI primary, Anthropic fallback)
3. **Ranking programs** against student profiles using a configurable 5-component weighted scoring system
4. **Serving ranked results** to the Orchestrator via authenticated HTTP endpoints

**Key Design Principles:**

- Single responsibility — crawl, extract, rank, serve
- No direct frontend access — only the Orchestrator (port 8000) calls this service
- No ORM overhead — raw SQL with `aiomysql` async connection pool
- Ethical crawling — robots.txt compliance, configurable delays, user-agent rotation
- LLM cost tracking — every API call logged with token counts and cost

---

## Implementation status

### Implemented in this repository

| Area | Status |
|------|--------|
| FastAPI app, lifespan, DB pool, service-token auth | Done |
| Program search, detail, ranking (weighted scoring) | Done |
| Crawl jobs (on-demand + batch), status APIs | Done |
| Scrapy batch spiders + httpx on-demand crawler | Done |
| HTML + LLM extraction with provider fallback | Done |
| APScheduler weekly batch hook | Done |
| MySQL migrations (universities, programs, requirements, crawl jobs, LLM logs) | Done |
| Scripts: migrations, seed universities, service token, manual batch trigger | Done |
| Unit + integration tests, GitHub Actions CI (format, lint, test, mypy, bandit, Docker) | Done |
| Docker / Compose for app + MySQL | Done |

### Not implemented or out of scope here

| Item | Notes |
|------|--------|
| **Orchestrator contract** | The platform orchestrator may still call `POST /discover` with `{ user_id, profile }`. This service exposes `POST /api/v1/programs/search` with `ProgramSearchRequest`. Wire the orchestrator client or add a compatibility route when integrating. |
| **Country filter** | `country` on search is accepted but filtering may be partial until schema/query fully use it. |
| **Live DB field on `/health`** | Response currently returns a static `"database": "not_connected"` (same pattern as sibling agents). A pool ping would require a small enhancement if you need real connectivity in JSON. |

---

## Architecture

```
┌─────────────────────────────────────┐
│       Frontend (React + Vite)       │
│       (http://localhost:3000)       │
└──────────────┬──────────────────────┘
               │
               │ JWT Bearer Token
               ▼
┌──────────────────────────────────────────────────────┐
│          Orchestrator Service (8000)                  │
│          X-Service-Token                             │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│       Program Discovery Agent (8002)                 │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │  API Layer (FastAPI)                        │     │
│  │  POST /api/v1/programs/search               │     │
│  │  GET  /api/v1/programs/{id}                 │     │
│  │  POST /api/v1/programs/crawl                │     │
│  │  GET  /api/v1/programs/crawl/{job_id}       │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Service Layer                              │     │
│  │  ProgramService    (search, rank)           │     │
│  │  CrawlService      (job management)         │     │
│  │  RankingService    (weighted scoring)        │     │
│  │  LLMService        (OpenAI → Anthropic)     │     │
│  │  SchedulerService  (APScheduler batch)      │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Crawler Layer                              │     │
│  │  Scrapy Spiders    (batch crawling)         │     │
│  │  On-Demand Crawler (httpx + BeautifulSoup)  │     │
│  │  HTML Parser       (BeautifulSoup helpers)  │     │
│  │  LLM Parser        (structured extraction)  │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Repository Layer (Raw SQL / aiomysql)      │     │
│  │  ProgramRepository                          │     │
│  │  UniversityRepository                       │     │
│  │  RequirementRepository                      │     │
│  │  CrawlJobRepository                         │     │
│  │  LLMCallLogRepository                       │     │
│  └─────────────────────────────────────────────┘     │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
      ┌─────────────────┐
      │   MySQL 8.0     │
      │   (aiomysql)    │
      └─────────────────┘
```

---

## Features

- **Dual Crawling Strategy**: Scrapy batch crawls + BeautifulSoup on-demand
- **LLM-Assisted Extraction**: OpenAI (gpt-4o-mini) primary, Anthropic (claude-sonnet-4) fallback
- **Weighted Ranking**: Configurable 5-component scoring (field 40%, requirements 25%, ranking 15%, deadline 10%, tuition 10%)
- **Scheduled Crawls**: APScheduler for weekly batch updates
- **Service Auth**: X-Service-Token middleware (orchestrator-only access)
- **Raw SQL**: aiomysql with repository pattern (no ORM)
- **LLM Cost Tracking**: Token usage and cost per API call logged to database
- **Program Staleness**: Auto-flag programs not crawled in 30+ days
- **Graceful Degradation**: Falls back to regex extraction when LLM is unavailable
- **Docker-First**: Compose for local dev, Kubernetes-ready

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime (CI, Dockerfile, and local venv should match) |
| MySQL | 8.0+ | Database |
| Docker | 24.0+ | Containerised deployment (optional) |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/maugus0/ouroboros-ai-program-discovery.git
cd ouroboros-ai-program-discovery

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
DB_HOST=localhost
DB_NAME=ouroboros_program_db
DB_USERNAME=root
DB_PASSWORD=your_mysql_password

X_SERVICE_TOKEN=your-48-char-random-token
OPENAI_API_KEY=sk-your-openai-key
```

### 3. Generate Service Token

```bash
python scripts/generate_service_token.py
# Add output to .env as X_SERVICE_TOKEN
```

### 4. Database Setup

**Option A: Docker (Recommended)**

```bash
docker compose up mysql -d
docker compose logs -f mysql   # wait for "ready for connections"
```

**Option B: Local MySQL**

```bash
mysql -u root -p -e "CREATE DATABASE ouroboros_program_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 5. Run Migrations

```bash
python scripts/run_migrations.py
```

Expected output:

```
Running migration: 001_create_universities.sql
  ✓ 001_create_universities.sql applied
Running migration: 002_create_programs.sql
  ✓ 002_create_programs.sql applied
Running migration: 003_create_program_requirements.sql
  ✓ 003_create_program_requirements.sql applied
Running migration: 004_create_crawl_jobs.sql
  ✓ 004_create_crawl_jobs.sql applied
Running migration: 005_create_llm_call_logs.sql
  ✓ 005_create_llm_call_logs.sql applied

All migrations applied successfully.
```

### 6. Seed Universities

```bash
python scripts/seed_universities.py
```

### 7. Start the Service

```bash
chmod +x start.sh
./start.sh
# or: uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### 8. Verify Health

```bash
curl http://localhost:8002/health
# {"status":"healthy","version":"0.1.0","database":"not_connected"}
```

Swagger docs are available at `http://localhost:8002/docs`.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| **Database** ||||
| `DB_HOST` | No | `localhost` | MySQL host |
| `DB_PORT` | No | `3306` | MySQL port |
| `DB_NAME` | No | `ouroboros_program_db` | Database name |
| `DB_USERNAME` | No | `root` | MySQL user |
| `DB_PASSWORD` | Yes | — | MySQL password |
| `DB_POOL_SIZE` | No | `10` | Max connections in pool |
| **Inter-Service Auth** ||||
| `X_SERVICE_TOKEN` | Yes | — | Shared secret for orchestrator calls |
| **LLM Configuration** ||||
| `OPENAI_API_KEY` | No | — | OpenAI API key (primary) |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model |
| `OPENAI_TEMPERATURE` | No | `0.1` | Low for structured extraction |
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key (fallback) |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Anthropic model |
| **Crawling** ||||
| `SCRAPY_CONCURRENT_REQUESTS` | No | `8` | Max concurrent crawl requests |
| `SCRAPY_DOWNLOAD_DELAY` | No | `2.0` | Seconds between requests |
| `RESPECT_ROBOTS_TXT` | No | `true` | Obey robots.txt |
| `PROGRAM_STALENESS_DAYS` | No | `30` | Re-crawl after N days |
| `BATCH_CRAWL_CRON` | No | `0 2 * * 0` | Weekly batch schedule |
| **Ranking Weights** ||||
| `RANKING_WEIGHT_FIELD_RELEVANCE` | No | `40` | Field match weight |
| `RANKING_WEIGHT_REQUIREMENT_MATCH` | No | `25` | Prereq match weight |
| `RANKING_WEIGHT_UNIVERSITY_RANKING` | No | `15` | University rank weight |
| `RANKING_WEIGHT_DEADLINE_PROXIMITY` | No | `10` | Deadline weight |
| `RANKING_WEIGHT_TUITION_AFFORDABILITY` | No | `10` | Tuition weight |
| **Application** ||||
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `USE_MOCK_DATA` | No | `true` | Use mocks in tests |
| `ALLOW_DB_FAILURE` | No | `false` | Continue if DB unavailable |
| **Docker** ||||
| `DOCKER_MYSQL_PORT` | No | `3309` | Host port for MySQL |

### Docker / CI Prefix Compatibility

The service also reads `MYSQL_*` variables for Docker/CI environments:

| `DB_*` Prefix | Equivalent `MYSQL_*` |
|---------------|---------------------|
| `DB_HOST` | `MYSQL_HOST` |
| `DB_NAME` | `MYSQL_DATABASE` |
| `DB_USERNAME` | `MYSQL_USER` |
| `DB_PASSWORD` | `MYSQL_PASSWORD` |
| `DB_PORT` | `MYSQL_PORT` |

---

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `universities` | Top university metadata with QS/THE rankings |
| `programs` | Crawled program details with JSON requirements |
| `program_requirements` | Granular requirement entries per program |
| `crawl_jobs` | Async crawl job tracking |
| `llm_call_logs` | LLM usage audit trail with cost tracking |

### Relationships

```
universities    (1) ──< (N) programs
programs        (1) ──< (N) program_requirements
```

### Migrations

Run in order via `python scripts/run_migrations.py`:

```
migrations/
├── 001_create_universities.sql
├── 002_create_programs.sql
├── 003_create_program_requirements.sql
├── 004_create_crawl_jobs.sql
└── 005_create_llm_call_logs.sql
```

---

## API Endpoints

**Base URL**: `http://localhost:8002`

All endpoints except health checks require the `X-Service-Token` header.

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Root health check |
| GET | `/health` | No | Detailed health status |

**GET `/` response:**

```json
{
  "message": "Program Discovery Agent",
  "version": "0.1.0",
  "status": "healthy"
}
```

**GET `/health` response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "not_connected"
}
```

The `database` field is a static placeholder for parity with other agents; it does not reflect a live pool check.

### Program Search

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/programs/search` | X-Service-Token | Search and rank programs |
| GET | `/api/v1/programs/{program_id}` | X-Service-Token | Get full program details + requirements |

**POST `/api/v1/programs/search` — request body:**

```json
{
  "field": "Computer Science",
  "degree_type": "master_research",
  "country": "United States",
  "student_profile": {
    "gpa": 3.8,
    "gpa_scale": 4.0,
    "prerequisites": ["Calculus", "Linear Algebra"],
    "research_interests": "machine learning",
    "target_field": "Computer Science",
    "budget_usd": 60000
  },
  "max_results": 20,
  "page": 1
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `field` | string | No | null | Field of study filter |
| `degree_type` | enum | No | null | `bachelor`, `master_coursework`, `master_research`, `phd` |
| `country` | string | No | null | Country filter (reserved for future filtering) |
| `student_profile` | object | No | null | Student data for ranking |
| `max_results` | int | No | 20 | Max results per page (1-100) |
| `page` | int | No | 1 | Page number |

**POST `/api/v1/programs/search` — response (200):**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "university_name": "MIT",
      "program_name": "MSc Computer Science",
      "degree_type": "master_research",
      "field": "Computer Science",
      "field_category": "STEM",
      "description": "...",
      "requirements": {"min_gpa": 3.5, "prerequisites": ["Calculus"]},
      "deadline": "2026-12-15",
      "tuition_usd": 55000.00,
      "duration_years": 2.0,
      "ranking_score": 95.0,
      "source_url": "https://mit.edu/cs/ms",
      "country": "United States",
      "university_ranking": 1,
      "crawled_at": "2026-03-15T10:00:00",
      "match_score": 87.5
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

**GET `/api/v1/programs/{program_id}` — response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "university_name": "MIT",
    "program_name": "MSc Computer Science"
  },
  "requirements": [
    {"id": "uuid", "requirement_type": "min_gpa", "requirement_value": "3.5", "is_mandatory": true},
    {"id": "uuid", "requirement_type": "language_test", "requirement_value": "IELTS 7.0", "is_mandatory": true}
  ]
}
```

### Crawl Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/programs/crawl` | X-Service-Token | Trigger on-demand or batch crawl (background task) |
| GET | `/api/v1/programs/crawl/{job_id}` | X-Service-Token | Get crawl job status |
| GET | `/api/v1/programs/crawl` | X-Service-Token | List crawl jobs |

**POST `/api/v1/programs/crawl` — request body:**

```json
{
  "job_type": "on_demand",
  "target_url": "https://university.edu/programs/cs-master",
  "target_university_id": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_type` | enum | No | `on_demand` (default) or `batch` |
| `target_url` | string | Conditional | URL to crawl (on-demand with URL) |
| `target_university_id` | string | No | Re-crawl all programs for this university |

**GET `/api/v1/programs/crawl` — query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 20 | Max results |
| `offset` | int | 0 | Pagination offset |
| `status` | string | null | `pending`, `running`, `completed`, `failed` |

### Error Responses

```json
{
  "success": false,
  "message": "Description of what went wrong"
}
```

| Status | Meaning |
|--------|---------|
| 401 | Missing `X-Service-Token` header |
| 403 | Invalid `X-Service-Token` |
| 404 | Resource not found |
| 422 | Validation error |
| 502 | Upstream error (LLM, crawl failure) |
| 503 | Service unavailable (database down) |

Interactive docs: `http://localhost:8002/docs`.

---

## Prompt System

Prompts are **JSON templates** in `prompts/` and are loaded at runtime with optional context injection (see `app/utils/prompt_utils.py` and `app/llm/prompts.py`).

### Template shape

Each file follows:

```json
{
  "prompt_template": {
    "base": {
      "agent_identity": { "role": "...", "service": "..." },
      "task_instructions": { "..." : "..." },
      "output_format": { "format": "json", "schema": { "..." : "..." } }
    }
  }
}
```

### Runtime context

Use `build_prompt_json` / `build_prompt_text` (or the helpers in `app/llm/prompts.py`) to merge runtime metadata before sending to the LLM.

### Available prompts

| File | Purpose |
|------|---------|
| `program_extraction_v1.json` | Extract structured program fields from page text |
| `requirement_parsing_v1.json` | Parse natural-language requirements into structured rows |
| `field_classification_v1.json` | Classify program field and broad category |

---

## Ranking Algorithm

Programs are ranked with a **weighted scoring system**: each component scores 0–1, multiplied by its weight; the final `match_score` is a 0–100 weighted average.

### Default weights (must sum to 100)

| Component | Weight | Description |
|-----------|--------|-------------|
| **Field Relevance** | 40% | Keyword overlap between student `target_field` and program `field` / name / description |
| **Requirement Match** | 25% | GPA vs `min_gpa`, prerequisite list overlap |
| **University Ranking** | 15% | Log-scaled prestige from QS/THE-style rank |
| **Deadline Proximity** | 10% | More time until deadline scores higher |
| **Tuition Affordability** | 10% | Lower tuition vs `budget_usd` (or absolute bands) |

### Component algorithms

**1. Field relevance** — Tokenize `target_field`; count matches in `field`, `program_name`, `description`; score = matched / total words; no profile → 0.5.

**2. Requirement match** — Normalize GPA to 4.0 scale vs `requirements.min_gpa`; compare `student_profile.prerequisites` to program prerequisites; empty requirements → 0.8.

**3. University ranking** — `score = 1.0 − log(rank) / log(500)`; unranked → 0.3.

**4. Deadline proximity** — `score = min(1, days_until_deadline / 365)`; past deadline → 0; no deadline → 0.5.

**5. Tuition** — With budget: ≤ budget → 1.0, ≤ 1.5× budget → 0.5, else 0.2. Without budget: tiered bands ($10k / $30k / $60k).

### Formula

```
total_score = Σ (component_score × component_weight) / Σ weights × 100
```

### Customization

```bash
RANKING_WEIGHT_FIELD_RELEVANCE=40
RANKING_WEIGHT_REQUIREMENT_MATCH=25
RANKING_WEIGHT_UNIVERSITY_RANKING=15
RANKING_WEIGHT_DEADLINE_PROXIMITY=10
RANKING_WEIGHT_TUITION_AFFORDABILITY=10
```

Example: favour affordability over prestige — lower `RANKING_WEIGHT_UNIVERSITY_RANKING` and raise `RANKING_WEIGHT_TUITION_AFFORDABILITY` (keep sum 100).

### Example

Student: CS master’s, GPA 3.8, budget $50k. ETH can outrank MIT on this service when tuition affordability dominates, even if MIT’s university rank is higher.

---

## Crawling Strategy

The agent uses a **dual crawling strategy**: batch coverage plus on-demand lookups.

### Batch mode (Scrapy)

- **Purpose**: Systematic crawling of configured universities
- **Schedule**: Weekly (Sunday 2 AM UTC) via APScheduler (`BATCH_CRAWL_CRON`)
- **Concurrency**: Up to 8 simultaneous requests across domains; 4 per domain
- **Scope**: Seeded universities and discovered program links

```
APScheduler → CrawlService → Scrapy spiders → validation pipelines → DB
```

### On-demand mode (httpx + BeautifulSoup)

- **Purpose**: Targeted scrape when the orchestrator needs a specific URL or university refresh
- **Latency**: Roughly single-page fetch + optional LLM extraction (order of seconds to tens of seconds)

```
Orchestrator → POST /api/v1/programs/crawl → httpx → parse → LLM (optional) → DB
```

### Ethics and rate limiting

| Setting | Default | Description |
|---------|---------|-------------|
| `ROBOTSTXT_OBEY` | `True` | Respect robots.txt |
| `SCRAPY_DOWNLOAD_DELAY` | `2.0` | Minimum seconds between Scrapy requests |
| `MIN_CRAWL_DELAY_SECONDS` / `MAX_CRAWL_DELAY_SECONDS` | `2` / `5` | On-demand jittered delay |
| `SCRAPY_CONCURRENT_REQUESTS` | `8` | Global concurrency cap |

User agents rotate (6+ realistic strings). Scrapy autothrottle backs off under load (start 2s, max 10s delay, target ~2 req/s).

### Program staleness

Programs older than `PROGRAM_STALENESS_DAYS` (default 30) are candidates for re-crawl so deadlines, tuition, and discontinuations stay fresh.

### LLM-assisted extraction

Pipeline: HTML → strip nav/scripts → text → LLM JSON → DB. **Fallback chain**: OpenAI (primary) → Anthropic → regex/heuristic extraction. Token usage and cost can be recorded via `llm_call_logs` / `LLMCallLogRepository` for budgeting.

---

## Development Workflow

### Code Quality Checks

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint
flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503,E501
pylint app/ tests/

# Type check
mypy app/ --ignore-missing-imports --no-strict-optional

# Run tests
ALLOW_DB_FAILURE=true USE_MOCK_DATA=true X_SERVICE_TOKEN=test-service-token pytest tests/ -v
```

### Pre-Commit Script

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
chmod +x pre-commit-check.sh
./pre-commit-check.sh
```

Runs Black, isort, flake8, pylint, syntax validation, tests, and mypy in sequence. Use an activated virtual environment so those tools are on your `PATH` (the script auto-activates `.venv`, `venv`, or `env` if present).

---

## Testing

### Run All Tests

```bash
ALLOW_DB_FAILURE=true USE_MOCK_DATA=true X_SERVICE_TOKEN=test-service-token pytest tests/ -v
```

### Run with Coverage

```bash
ALLOW_DB_FAILURE=true USE_MOCK_DATA=true X_SERVICE_TOKEN=test-service-token pytest tests/ --cov=app --cov-report=html -v
open htmlcov/index.html
```

Pytest picks up **`pytest.ini`** (paths, `addopts`, `filterwarnings`) and mirrors the same options under `[tool.pytest.ini_options]` in **`pyproject.toml`** for editors and tooling — matching the Student Profile agent layout.

### Test Structure

```
tests/
├── conftest.py                         # Shared fixtures
├── fake_repos.py                       # In-memory repository mocks
├── unit/
│   ├── test_config.py                  # Configuration loading
│   ├── test_health.py                  # Health check endpoints
│   ├── test_main.py                    # FastAPI application
│   ├── test_security.py                # X-Service-Token validation
│   ├── test_exceptions.py              # Custom exception classes
│   ├── test_models.py                  # Pydantic model validation
│   ├── test_ranking_service.py         # Weighted scoring logic
│   ├── test_llm_service.py             # LLM fallback (mocked)
│   ├── test_llm_prompts.py             # Prompt template loading
│   ├── test_prompt_utils.py            # Prompt building utilities
│   ├── test_html_parser.py             # BeautifulSoup extraction
│   ├── test_html_utils.py              # URL/HTML utility functions
│   └── test_scrapy_pipeline.py         # Scrapy data validation
└── integration/
    ├── test_program_search_flow.py     # HTTP search + ranking
    └── test_crawl_job_flow.py          # HTTP crawl trigger + status
```

---

## CI/CD Pipeline

**Workflow**: `.github/workflows/deploy.yml` (named **OuroborosAI Program Discovery CI/CD Pipeline** in GitHub)

**Triggers**: Pull requests to `main` / `develop` (opened, synchronize, reopened); pushes to `main`.

**Concurrency**: One run per workflow + ref; newer commits cancel in-progress runs on the same ref.

**Python version**: CI uses **3.11** (`PYTHON_VERSION` in the workflow), matching **`python:3.11-slim`** in the Dockerfile so the image you push to GHCR is the same language version as lint/tests and local tooling (`pyproject.toml`, mypy, Black target).

Shared lint rules live in `.pylintrc` (line length, docstring / design relaxations, similarity thresholds). **Bandit** uses root `bandit.yaml` (documented suppressions for known-safe patterns). The `if __name__ == "__main__"` dev server binds **127.0.0.1**; production still listens on **0.0.0.0** via the Dockerfile `CMD`.

### Pipeline Stages

| Stage | Description |
|-------|-------------|
| **Format** | Black + isort (pip cache) |
| **Lint** | flake8 + pylint (pip cache) |
| **Unit Tests** | `pytest tests/unit/` + JUnit XML artifact |
| **Type Check** | mypy after format + lint + unit tests |
| **Tests + Coverage** | Full `pytest tests/` + HTML + Cobertura XML artifacts |
| **Bandit** | Static scan with `bandit.yaml` (fails the job on new findings outside config) |
| **Snyk OSS** | Dependency scan when `SNYK_TOKEN` is set; otherwise logs a skip message |
| **Docker** | Build on every run; **push to `ghcr.io/<owner>/<repo>`** only on merge to `main` |
| **Trivy** | Container scan on **push to `main`** only (pulls image by commit SHA from GHCR) |
| **Summary** | Uploads `ci-reports` artifact with job outcomes |

Optional: set repository variable `ENABLE_CODE_SCANNING_SARIF` to `true` to upload Snyk/Trivy SARIF to GitHub Code Scanning (guarded for forks on PRs).

### Pipeline Graph

```
format ───┐
lint    ──┼──> type-check ──────┐
unit-tests┘                     ├──> docker-build ──> Trivy (main only)
          ├──> integration-tests┤
          ├──> security-static (Bandit)
          └──> security-scan (Snyk)

docker-build (PR: build+load only; main: push GHCR)

reports-summary (always; includes skipped Trivy on PRs)
```

### Local CI Simulation

```bash
black --check app/ tests/
isort --check-only app/ tests/
flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503,E501
pylint app/ tests/ --max-line-length=120 --disable=C0111,R0903
mypy app/ --ignore-missing-imports --no-strict-optional
ALLOW_DB_FAILURE=true USE_MOCK_DATA=true X_SERVICE_TOKEN=test-service-token pytest tests/ -v
bandit -r app/ -c bandit.yaml
docker build -t program-discovery-agent .
```

---

## Deployment

### Docker Compose (full stack)

```bash
docker compose up --build -d
docker compose logs -f
docker compose down
docker compose down -v
```

### MySQL only (app on host)

```bash
docker compose up mysql -d
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker image only

```bash
docker build -t program-discovery-agent:latest .

docker run -d \
  --name program-discovery \
  -p 8002:8002 \
  -e DB_HOST=mysql-host \
  -e DB_PORT=3306 \
  -e DB_NAME=ouroboros_program_db \
  -e DB_PASSWORD=secure-password \
  -e X_SERVICE_TOKEN=your-48-char-token \
  -e OPENAI_API_KEY=sk-your-key \
  -e ALLOW_DB_FAILURE=false \
  -e LOG_LEVEL=INFO \
  program-discovery-agent:latest
```

### Migrations and seed data

```bash
python scripts/run_migrations.py
python scripts/seed_universities.py
```

### Port assignments (platform)

| Service | HTTP port | Notes |
|---------|-----------|--------|
| Orchestrator | 8000 | |
| Student Profile | 8001 | |
| **Program Discovery** | **8002** | This service |
| Scholarship Discovery | 8003 | |
| Eligibility Engine | 8004 | |
| Application Support | 8005 | |

**MySQL host ports** (avoid collisions): Orchestrator 3307, Student Profile 3308, **Program Discovery 3309** (`DOCKER_MYSQL_PORT`).

### Production checklist

- Set `DB_PASSWORD`, `X_SERVICE_TOKEN` (see `scripts/generate_service_token.py`), and `OPENAI_API_KEY` for real extraction.
- Use `ALLOW_DB_FAILURE=false` and `LOG_LEVEL=INFO` in production.
- See `.env.example` for the full variable list.

---

## Project Structure

```
ouroboros-ai-program-discovery/
├── app/
│   ├── api/                            # Route handlers (thin layer)
│   │   ├── health.py                   # GET / and /health
│   │   ├── programs.py                 # POST /search, GET /{id}
│   │   └── crawl.py                    # POST /crawl, GET /crawl/{id}
│   ├── core/                           # Infrastructure
│   │   ├── logging.py                  # structlog configuration
│   │   └── security.py                 # X-Service-Token validation
│   ├── crawlers/                       # Web crawling layer
│   │   ├── scrapy/                     # Batch crawling
│   │   │   ├── spiders/                # Scrapy spider classes
│   │   │   ├── middlewares.py          # User-agent rotation
│   │   │   ├── pipelines.py           # Data validation + storage
│   │   │   └── settings.py            # Scrapy config
│   │   ├── parsers/                    # Page parsing
│   │   │   ├── html_parser.py         # BeautifulSoup helpers
│   │   │   └── llm_parser.py          # LLM-assisted extraction
│   │   └── on_demand_crawler.py       # httpx-based targeted scraping
│   ├── llm/                            # LLM integration
│   │   ├── openai_client.py           # Primary provider + retry
│   │   ├── anthropic_client.py        # Fallback provider + retry
│   │   ├── prompts.py                 # Prompt builder functions
│   │   └── schemas.py                 # Output validation schemas
│   ├── models/                         # Pydantic request/response schemas
│   │   ├── common_models.py           # StandardResponse, pagination
│   │   ├── program.py                 # Search request/response
│   │   ├── crawl.py                   # Crawl job models
│   │   └── ranking.py                 # Ranking weights/breakdown
│   ├── repositories/                   # Raw SQL data access (aiomysql)
│   │   ├── db_pool.py                 # Connection pool management
│   │   ├── mysql_base.py             # Base repository
│   │   ├── mysql_program_repo.py     # Programs CRUD + search
│   │   ├── mysql_university_repo.py  # Universities CRUD
│   │   ├── mysql_requirement_repo.py # Requirements CRUD
│   │   ├── mysql_crawl_job_repo.py   # Crawl job tracking
│   │   └── mysql_llm_call_log_repo.py # LLM audit logging
│   ├── services/                       # Business logic
│   │   ├── program_service.py        # Search + rank orchestration
│   │   ├── crawl_service.py          # Crawl job management
│   │   ├── llm_service.py            # LLM provider fallback
│   │   ├── ranking_service.py        # Weighted scoring
│   │   └── scheduler_service.py      # APScheduler batch crawls
│   ├── middleware/                      # HTTP middleware
│   │   ├── service_auth.py           # X-Service-Token dependency
│   │   └── logging_middleware.py     # Trace ID + latency logging
│   ├── utils/                          # Utilities
│   │   ├── exceptions.py             # Custom exception hierarchy
│   │   ├── trace_id.py               # UUID-v4 trace ID
│   │   ├── helpers.py                # generate_uuid, timestamps
│   │   ├── timezone.py               # UTC helpers
│   │   ├── prompt_utils.py           # JSON template loading
│   │   └── html_utils.py             # URL validation, text cleaning
│   ├── config.py                       # Pydantic settings
│   └── main.py                         # FastAPI app with lifespan
├── migrations/                         # SQL migration files (001-005), same layout as other agents
├── prompts/                            # JSON prompt templates
│   ├── program_extraction_v1.json
│   ├── requirement_parsing_v1.json
│   └── field_classification_v1.json
├── scripts/
│   ├── run_migrations.py              # Execute migrations
│   ├── seed_universities.py           # Load top 50 universities
│   ├── generate_service_token.py      # Generate X_SERVICE_TOKEN
│   └── trigger_batch_crawl.py         # Manual batch crawl
├── tests/
│   ├── unit/                           # Unit tests
│   └── integration/                    # Integration tests
├── .github/workflows/
│   └── deploy.yml                      # 7-job CI/CD pipeline
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── pytest.ini
├── .flake8
├── bandit.yaml
├── .pylintrc
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── start.sh
├── pre-commit-check.sh
└── README.md
```

---

## Troubleshooting

### Database Connection Failed

**Symptom**: `RuntimeError: Database pool has not been initialised`

```bash
# Check MySQL is running
docker compose ps

# Test connection
mysql -h localhost -P 3309 -u root -p -e "SHOW DATABASES;"

# Verify credentials
grep DB_ .env
```

### LLM Extraction Fails

**Symptom**: `LLMExtractionError: Both LLM providers failed`

```bash
# Verify API keys
grep API_KEY .env

# Test OpenAI connectivity
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Check LLM call logs (requires DB)
mysql -e "SELECT * FROM llm_call_logs ORDER BY created_at DESC LIMIT 5;"
```

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'app'`

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Crawl Jobs Stay Pending

**Symptom**: Crawl jobs created but never start

```bash
# Check if the scheduler is running (look for "scheduler_started" in logs)
docker compose logs program-discovery | grep scheduler

# Manually trigger a crawl
python scripts/trigger_batch_crawl.py
```

---

## Attribution

**Developed by**: OuroborosAI Developer Team

**Project**: Ouroboros AI Scholarship Discovery Platform

**Repository**: [github.com/maugus0/ouroboros-ai-program-discovery](https://github.com/maugus0/ouroboros-ai-program-discovery)

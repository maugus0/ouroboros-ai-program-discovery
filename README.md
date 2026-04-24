# Ouroboros Program Discovery Agent

Microservice for the **Ouroboros AI** scholarship discovery platform. The Program Discovery Agent searches, ranks, and answers questions about academic programs using LLM (OpenAI/Anthropic with intelligent fallback), manages institution data with QS World Rankings integration, and stores data in MySQL using raw SQL with a repository pattern.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [LLM Integration](#llm-integration)
- [Crawling System](#crawling-system)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Attribution](#attribution)

---

## Overview

The Program Discovery Agent is a critical microservice in the Ouroboros AI platform that:

1. **Searches and ranks programs** based on student profiles, preferences, and weighted criteria
2. **Answers questions** about programs using LLM with natural language understanding
3. **Manages institution data** with 1500+ universities from QS World Rankings 2026
4. **Crawls university websites** for up-to-date program information (Scrapy-based)
5. **Integrates with orchestrator** via internal JWT authentication

**Key Design Principles:**

- No direct frontend access — only the orchestrator calls this service via internal JWT
- No ORM overhead — raw SQL with `aiomysql` async connection pool
- LLM resilience — OpenAI primary, Anthropic fallback with retry logic
- Weighted ranking algorithm — configurable weights summing to 100%
- QS Rankings integration — 1504 universities with detailed indicator scores

---

## Architecture

```
┌─────────────────────────────────────┐
│    Orchestrator Service (8000)      │
│    (Single Entry Point)             │
└──────────────┬──────────────────────┘
               │
               │ Internal JWT Bearer Token
               ▼
┌──────────────────────────────────────────────────────┐
│       Program Discovery Agent (8002)                  │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │  API Layer (FastAPI)                        │     │
│  │  GET  /health                               │     │
│  │  GET  /institutions, /institutions/{id}    │     │
│  │  GET  /programs, /programs/{id}            │     │
│  │  POST /programs/rank                        │     │
│  │  POST /chat/ask, /chat/extract-intent      │     │
│  │  POST /crawl/jobs, GET /crawl/jobs/{id}    │     │
│  │  GET  /admin/llm/logs, /admin/llm/stats    │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Service Layer                              │     │
│  │  InstitutionService, ProgramService         │     │
│  │  RankingService (weighted algorithm)        │     │
│  │  LLMService (OpenAI → Anthropic fallback)   │     │
│  │  CrawlerService (Scrapy orchestration)      │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Repository Layer (Raw SQL)                 │     │
│  │  InstitutionRepo, ProgramRepo               │     │
│  │  InstitutionRankingRepo, LLMCallLogRepo     │     │
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

### Program Data Crawling (ORB-30)

- **Scrapy-based framework** with configurable selectors
- **Sample configurations** for MIT, Stanford, Oxford
- **Robots.txt compliance** and rate limiting
- **Crawl job tracking** with status and metrics
- **Stale detection** — programs marked stale after 30 days

### Program Search & Ranking (ORB-31)

- **Advanced filtering** — field, degree level, location, tuition, deadlines, language
- **Weighted ranking algorithm** — configurable weights (must sum to 100):
  - Field relevance: 40%
  - Requirements match: 25%
  - University ranking: 15%
  - Deadline proximity: 10%
  - Tuition affordability: 10%
- **Pagination** — cursor-based, default 20 programs per page
- **Individual program details** with requirements breakdown

### Institution Management

- **1504 universities** from QS World Rankings 2026
- **Multi-source rankings** — QS, THE, ARWU, US News support
- **Detailed indicators** — academic reputation, employer reputation, faculty ratio, citations, international ratios
- **Slug-based deduplication** — prevents duplicate entries during crawling

### LLM-Powered Q&A

- **Natural language questions** about programs, deadlines, requirements
- **Intent extraction** — parse queries into structured search filters
- **Eligibility assessment** — check student fit for programs
- **Program comparison** — side-by-side analysis
- **Provider fallback** — OpenAI primary, Anthropic secondary
- **Call logging** — all LLM calls logged with tokens, latency, and status

### Admin & Monitoring

- **LLM usage tracking** — view call logs and usage statistics
- **Token monitoring** — track input/output tokens per provider
- **Error tracking** — monitor failed LLM calls with error messages
- **Latency metrics** — measure response times per model

---

## Prerequisites

| Tool              | Version | Purpose                                          |
| ----------------- | ------- | ------------------------------------------------ |
| Python            | 3.11+   | Runtime                                          |
| MySQL             | 8.0+    | Database                                         |
| OpenAI API Key    | —       | Primary LLM provider                             |
| Anthropic API Key | —       | Fallback LLM provider (optional but recommended) |
| Docker            | 24.0+   | Containerised deployment (optional)              |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/maugus0/ouroboros-ai-program-discovery.git
cd ouroboros-ai-program-discovery

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Database
DB_HOST=localhost
DB_NAME=ouroboros_program_db
DB_USERNAME=root
DB_PASSWORD=your_mysql_password

# LLM Keys (copy from Student Profile Agent .env)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Internal Auth (copy public key from orchestrator)
INTERNAL_TOKEN_VERIFY_ENABLED=true
INTERNAL_TOKEN_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```

See [Configuration](#configuration) for the full reference.

### 3. Database Setup

**Option A: Docker (Recommended)**

```bash
docker compose up mysql -d
docker compose logs -f mysql   # wait for "ready for connections"
```

**Option B: Local MySQL**

Ensure MySQL is running. No need to create the database manually — the migration script handles it.

### 4. Run Migrations

The migration script will:
- Create the database if it doesn't exist
- Run all SQL migrations in order (001-006)
- Skip already-applied migrations (idempotent)

```bash
python scripts/run_migrations.py
```

Expected output:

```
Starting migrations for database: ouroboros_program_db
Database 'ouroboros_program_db' ready
Found 6 migration file(s)
Running migration: 001_create_institutions.sql
  ✓ 001_create_institutions.sql applied
Running migration: 002_create_institution_rankings.sql
  ✓ 002_create_institution_rankings.sql applied
Running migration: 003_create_programs.sql
  ✓ 003_create_programs.sql applied
Running migration: 004_create_program_requirements.sql
  ✓ 004_create_program_requirements.sql applied
Running migration: 005_create_crawl_jobs.sql
  ✓ 005_create_crawl_jobs.sql applied
Running migration: 006_create_llm_call_logs.sql
  ✓ 006_create_llm_call_logs.sql applied
All migrations completed successfully!
Database connection closed
```

### 5. Generate and Seed QS Rankings Data

```bash
# Generate JSON from QS Excel file (1504 universities)
python scripts/generate_qs_json.py

# Seed institutions and rankings into database
python scripts/seed_qs_rankings.py

# Seed sample programs for top universities
python scripts/seed_sample_programs.py
```

Expected output:

```
Generated 1504 institutions to data/qs_world_rankings_2026.json
Seeding 1504 institutions...
  Seeded 100/1504 institutions
  ...
Done! Seeded 1504 institutions with QS 2026 rankings.
```

### 5c. Seed Singapore CS Programs (Recommended)

Seed additional Computer Science and related programs from Singapore universities (NTU, SMU, SUTD):

```bash
python scripts/seed_singapore_cs_programs.py
```

This seeds **11 programs** including:
- **NTU**: MSc Data Science, MSc AI, Master of Computing in Applied AI, MSc Cyber Security, MSc Blockchain
- **SMU**: MSc Computing, Master of IT in Business (Analytics Track)
- **SUTD**: MSc Technology & Design (AI), MSc Technology & Design (Cybersecurity), MSc Design & AI for Enterprise, MSc Security by Design

Expected output:

```
=== Nanyang Technological University, Singapore (NTU Singapore) ===
  + Created: Master of Science in Data Science (...)
  + Created: Master of Science in Artificial Intelligence (...)
  ...
=== Singapore Management University ===
  + Created: Master of Science in Computing (...)
  ...
=== Singapore University of Technology and Design ===
  + Created: Master of Science in Technology and Design (Artificial Intelligence) (...)
  ...

✓ Seeded 11 programs with 0 requirements
```

> **Note**: Run this after `seed_qs_rankings.py` as it requires institutions to exist.

### 5b. (Optional) Enrich Institution Data

The QS rankings data doesn't include city, website URL, or institution type. Use the enrichment script to fill in missing fields using LLM:

```bash
# Preview what would be updated (dry run)
python scripts/enrich_institutions.py --dry-run --limit 10

# Enrich first 50 institutions
python scripts/enrich_institutions.py --limit 50

# Enrich all institutions (may take a while)
python scripts/enrich_institutions.py
```

The script uses OpenAI to infer:
- **city** — from institution name
- **website_url** — official website
- **institution_type** — public/private/private_not_for_profit

### 6. Start the Service

```bash
./start.sh
# or: python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### 7. Verify Health

```bash
curl http://localhost:8002/health
```

Expected response:

```json
{"status": "healthy", "version": "0.2.0", "database": "connected", "timestamp": "2026-04-21T..."}
```

**Swagger UI**: http://localhost:8002/docs

---

## Configuration

### Environment Variables

| Variable                          | Required | Default                           | Description                                     |
| --------------------------------- | -------- | --------------------------------- | ----------------------------------------------- |
| **Database**                      |          |                                   |                                                 |
| `DB_HOST`                         | No       | `localhost`                       | MySQL host                                      |
| `DB_PORT`                         | No       | `3306`                            | MySQL port                                      |
| `DB_NAME`                         | No       | `ouroboros_program_db`            | Database name                                   |
| `DB_USERNAME`                     | No       | `root`                            | MySQL user                                      |
| `DB_PASSWORD`                     | Yes      | —                                 | MySQL password                                  |
| `DB_POOL_SIZE`                    | No       | `10`                              | Max connections in pool                         |
| `DB_POOL_NAME`                    | No       | `program_discovery_pool`          | Connection pool name                            |
| `DB_CONNECTION_TIMEOUT`           | No       | `20`                              | Connection timeout in seconds                   |
| `DOCKER_MYSQL_PORT`               | No       | `3309`                            | Host port for Docker MySQL                      |
| **Inter-Service Auth**            |          |                                   |                                                 |
| `INTERNAL_TOKEN_VERIFY_ENABLED`   | No       | `false`                           | Enable JWT verification                         |
| `INTERNAL_TOKEN_SIGNING_ALGORITHM`| No       | `RS256`                           | JWT signing algorithm                           |
| `INTERNAL_TOKEN_PUBLIC_KEY`       | No       | —                                 | RSA public key PEM (escape newlines as `\n`)    |
| `INTERNAL_TOKEN_JWKS_URL`         | No       | —                                 | JWKS endpoint URL for key fetching              |
| `INTERNAL_TOKEN_AUDIENCE`         | No       | `ouroboros.program-discovery`     | Expected JWT audience claim                     |
| `INTERNAL_TOKEN_ISSUER`           | No       | `ouroboros-orchestrator-internal` | Expected JWT issuer claim                       |
| **LLM — OpenAI**                  |          |                                   |                                                 |
| `OPENAI_API_KEY`                  | Yes      | —                                 | OpenAI API key                                  |
| `OPENAI_MODEL`                    | No       | `gpt-4o-mini`                     | Model identifier                                |
| `OPENAI_MAX_TOKENS`               | No       | `2000`                            | Max output tokens                               |
| `OPENAI_TEMPERATURE`              | No       | `0.0`                             | Sampling temperature                            |
| **LLM — Anthropic**               |          |                                   |                                                 |
| `ANTHROPIC_API_KEY`               | Recommended | —                              | Anthropic API key (fallback)                    |
| `ANTHROPIC_MODEL`                 | No       | `claude-haiku-4-5-20251001`       | Model identifier                                |
| `ANTHROPIC_MAX_TOKENS`            | No       | `2000`                            | Max output tokens                               |
| `LLM_MAX_RETRIES`                 | No       | `3`                               | Max retries per provider call                   |
| `LLM_RETRY_DELAY`                 | No       | `2`                               | Retry delay (seconds)                           |
| **Ranking Weights**               |          |                                   |                                                 |
| `RANKING_WEIGHT_FIELD_RELEVANCE`  | No       | `40`                              | Field match weight (0-100)                      |
| `RANKING_WEIGHT_REQUIREMENT_MATCH`| No       | `25`                              | Requirements match weight                       |
| `RANKING_WEIGHT_UNIVERSITY_RANKING`| No      | `15`                              | University rank weight                          |
| `RANKING_WEIGHT_DEADLINE_PROXIMITY`| No      | `10`                              | Deadline proximity weight                       |
| `RANKING_WEIGHT_TUITION_AFFORDABILITY`| No   | `10`                              | Tuition affordability weight                    |
| **Crawling**                      |          |                                   |                                                 |
| `CRAWL_RESPECT_ROBOTS_TXT`        | No       | `true`                            | Respect robots.txt                              |
| `CRAWL_RATE_LIMIT_DELAY`          | No       | `2.0`                             | Delay between requests (seconds)                |
| `CRAWL_USER_AGENT`                | No       | `OuroborosCrawler/1.0`            | Crawler user agent string                       |
| `CRAWL_TIMEOUT_SECONDS`           | No       | `30`                              | Request timeout                                 |
| `CRAWL_STALE_DAYS`                | No       | `30`                              | Days before program marked stale                |
| **Application**                   |          |                                   |                                                 |
| `LOG_LEVEL`                       | No       | `INFO`                            | `DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL`         |
| `UVICORN_HOST`                    | No       | `127.0.0.1`                       | Server bind host                                |
| `UVICORN_PORT`                    | No       | `8002`                            | Server bind port                                |
| `USE_MOCK_DATA`                   | No       | `false`                           | Use mock data (tests only)                      |
| `ALLOW_DB_FAILURE`                | No       | `false`                           | Continue if DB unavailable (tests only)         |

### Docker / CI Prefix Compatibility

The service also reads `MYSQL_*` variables for Docker/CI environments:

| `DB_*` Prefix | Equivalent `MYSQL_*` |
| ------------- | -------------------- |
| `DB_HOST`     | `MYSQL_HOST`         |
| `DB_NAME`     | `MYSQL_DATABASE`     |
| `DB_USERNAME` | `MYSQL_USER`         |
| `DB_PASSWORD` | `MYSQL_PASSWORD`     |
| `DB_PORT`     | `MYSQL_PORT`         |

---

## Database Schema

### Tables

| Table                 | Purpose                                                           |
| --------------------- | ----------------------------------------------------------------- |
| `institutions`        | University data with slug-based deduplication                     |
| `institution_rankings`| Multi-source rankings (QS, THE, ARWU) with indicator scores       |
| `programs`            | Academic program details (name, degree, field, tuition, deadline) |
| `program_requirements`| GPA, test scores, language requirements per program               |
| `crawl_jobs`          | Crawl job tracking with status and metrics                        |
| `llm_call_logs`       | LLM API call audit trail (tokens, latency, errors)                |

### LLM Call Logs Schema

```sql
CREATE TABLE llm_call_logs (
    id CHAR(36) PRIMARY KEY,
    provider ENUM('openai', 'anthropic', 'other') NOT NULL,
    model VARCHAR(64) NOT NULL,
    purpose VARCHAR(128) NOT NULL,        -- e.g., 'program_qa', 'intent_extraction'
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    latency_ms INT,
    status ENUM('success', 'error', 'timeout') NOT NULL,
    error_message TEXT,                    -- error details if status='error'
    metadata JSON,                         -- optional extra data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Migrations

Run migrations via `python scripts/run_migrations.py`:

```
migrations/
├── 001_create_institutions.sql
├── 002_create_institution_rankings.sql
├── 003_create_programs.sql
├── 004_create_program_requirements.sql
├── 005_create_crawl_jobs.sql
└── 006_create_llm_call_logs.sql
```

The migration script:
- **Creates the database** if it doesn't exist
- **Runs all .sql files** in sorted numerical order
- **Skips already-applied** statements (idempotent — safe to re-run)
- **Validates database name** (alphanumeric + underscore only, max 64 chars)
- **Sets UTC timezone** for the connection session

---

## API Endpoints

**Base URL**: `http://localhost:8002`

All endpoints (except `/health`) require internal JWT authentication via `Authorization: Bearer <token>` header.

### Health

| Method | Path      | Auth | Description                  |
| ------ | --------- | ---- | ---------------------------- |
| GET    | `/health` | No   | Health check with DB status  |

### Institutions

| Method | Path                          | Description                       |
| ------ | ----------------------------- | --------------------------------- |
| GET    | `/institutions`               | Search institutions (paginated)   |
| GET    | `/institutions/countries`     | List all countries                |
| GET    | `/institutions/count`         | Get total institution count       |
| GET    | `/institutions/{id}`          | Get institution by ID             |
| GET    | `/institutions/{id}/rankings` | Get all rankings for institution  |

### Programs

| Method | Path                          | Description                       |
| ------ | ----------------------------- | --------------------------------- |
| GET    | `/programs`                   | Search programs with filters      |
| GET    | `/programs/fields`            | List all fields of study          |
| GET    | `/programs/field-categories`  | List field categories             |
| GET    | `/programs/count`             | Get total program count           |
| POST   | `/programs/rank`              | Rank programs for student profile |
| GET    | `/programs/{id}`              | Get program details               |
| GET    | `/programs/{id}/requirements` | Get program requirements          |

### Chat (LLM-Powered)

| Method | Path                   | Description                          |
| ------ | ---------------------- | ------------------------------------ |
| POST   | `/chat/ask`            | Ask questions about programs         |
| POST   | `/chat/extract-intent` | Extract search filters from text     |

### Crawl Jobs

| Method | Path              | Description              |
| ------ | ----------------- | ------------------------ |
| POST   | `/crawl/jobs`     | Create new crawl job     |
| GET    | `/crawl/jobs`     | List recent crawl jobs   |
| GET    | `/crawl/jobs/{id}`| Get crawl job status     |
| POST   | `/crawl/trigger`  | Trigger crawl (stubbed)  |

### Admin (Monitoring)

| Method | Path                | Description                              |
| ------ | ------------------- | ---------------------------------------- |
| GET    | `/admin/llm/logs`   | Get recent LLM call logs (limit param)   |
| GET    | `/admin/llm/stats`  | Get LLM usage stats by provider/model    |

**Query Parameters:**

- `/admin/llm/logs?limit=50` — Returns last N LLM calls (default: 50, max: 500)
- `/admin/llm/stats?days=30` — Returns stats for last N days (default: 30)

**Example Response (`/admin/llm/logs`):**

```json
{
  "count": 2,
  "logs": [
    {
      "id": "abc-123",
      "provider": "openai",
      "model": "gpt-4o-mini",
      "purpose": "program_qa",
      "input_tokens": 1234,
      "output_tokens": 567,
      "latency_ms": 1890,
      "status": "success",
      "error_message": null,
      "created_at": "2026-04-21T12:34:56"
    }
  ]
}
```

**Example Response (`/admin/llm/stats`):**

```json
{
  "stats": [
    {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "call_count": 150,
      "total_input_tokens": 45000,
      "total_output_tokens": 22000,
      "avg_latency_ms": 1200.5,
      "success_count": 148,
      "error_count": 2
    }
  ],
  "period_days": 30
}
```

---

## LLM Integration

### Providers

- **Primary**: OpenAI (`gpt-4o-mini` default)
- **Fallback**: Anthropic (`claude-haiku-4-5` default)

### Capabilities

| Feature              | Description                                           |
| -------------------- | ----------------------------------------------------- |
| **Program Q&A**      | Answer questions about programs, deadlines, tuition   |
| **Intent Extraction**| Parse "find CS programs in US" → structured filters   |
| **Eligibility Check**| Assess student fit against program requirements       |
| **Comparison**       | Compare multiple programs side-by-side                |
| **Institution Q&A**  | Answer questions using real QS ranking data           |

### Call Logging

All LLM calls are automatically logged to the `llm_call_logs` table with:

| Field          | Description                                      |
| -------------- | ------------------------------------------------ |
| `provider`     | `openai` or `anthropic`                          |
| `model`        | Model identifier (e.g., `gpt-4o-mini`)           |
| `purpose`      | Call type: `program_qa`, `intent_extraction`     |
| `input_tokens` | Number of input tokens                           |
| `output_tokens`| Number of output tokens                          |
| `latency_ms`   | Response time in milliseconds                    |
| `status`       | `success`, `error`, or `timeout`                 |
| `error_message`| Error details (if status is `error`)             |

View logs via the Admin API: `GET /admin/llm/logs`

### Example: Ask About Programs

```bash
curl -X POST http://localhost:8002/chat/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the best computer science programs in the US?",
    "filters": {"country": "United States", "field": "Computer Science"},
    "limit": 10
  }'
```

### Example: Ask About Universities (Uses Real Data)

```bash
curl -X POST http://localhost:8002/chat/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the top 50 universities in the QS World Rankings?"
  }'
```

The system automatically detects institution/ranking queries and fetches real data from the database instead of relying on LLM general knowledge.

---

## Crawling System

### Spider Architecture

```python
# Base spider with common functionality
class BaseProgramSpider(scrapy.Spider):
    # robots.txt compliance
    # rate limiting
    # data extraction helpers (tuition, deadline, duration)

# Configurable university spider
class UniversityProgramSpider(BaseProgramSpider):
    # CSS/XPath selector configuration
    # Automatic field categorization
    # Requirement classification
```

### Pre-Configured Universities

| University                         | Config Key |
| ---------------------------------- | ---------- |
| Massachusetts Institute of Technology | `mit`   |
| Stanford University                | `stanford` |
| University of Oxford               | `oxford`   |

---

## Development Workflow

### Code Quality Checks

```bash
# Format code
black app/ tests/ scripts/
isort app/ tests/ scripts/

# Lint
flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503,E501
pylint app/ tests/ --max-line-length=120 --disable=C0111,R0903,R0913,R0914,R0911,R0912,R0915,R0917,W0212,W0621,W0718,C0415,W0107,E0401

# Type check
mypy app/ --ignore-missing-imports --no-strict-optional

# Security scan
bandit -r app/ -c bandit.yaml
```

### Pre-Commit Script

```bash
chmod +x pre-commit-check.sh
./pre-commit-check.sh
```

Runs: Black, isort, flake8, pylint, syntax validation, pytest, mypy, and Bandit in sequence.

---

## Testing

### Run All Tests

```bash
ALLOW_DB_FAILURE=true USE_MOCK_DATA=true INTERNAL_TOKEN_VERIFY_ENABLED=false pytest tests/ -v
```

### Run with Coverage

```bash
ALLOW_DB_FAILURE=true USE_MOCK_DATA=true INTERNAL_TOKEN_VERIFY_ENABLED=false pytest tests/ --cov=app --cov-report=html -v
open htmlcov/index.html
```

### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── test_health.py             # Health endpoint tests
│   ├── test_ranking_service.py    # Ranking algorithm tests
│   └── test_models.py             # Pydantic model tests
└── integration/
    └── test_placeholder.py        # Integration test placeholder
```

---

## CI/CD Pipeline

**Workflow**: `.github/workflows/deploy.yml`

**Trigger**: Pull requests to `main` or `develop`

### Pipeline Stages

| Stage              | Description                                          |
| ------------------ | ---------------------------------------------------- |
| **Format**         | Black + isort validation                             |
| **Lint**           | flake8 + pylint (blocking)                           |
| **Unit Tests**     | `pytest tests/unit/` with JUnit XML artifact         |
| **Type Check**     | mypy — blocking                                      |
| **Tests + Coverage**| Full `pytest tests/` with coverage report           |
| **Security Audit** | Bandit static security analysis                      |
| **Docker Build**   | Verify image builds                                  |
| **Summary**        | Markdown table of all job results                    |

---

## Deployment

### Docker Compose (Full Stack)

```bash
docker compose up --build -d      # Start MySQL + service
docker compose logs -f            # Follow logs
docker compose down               # Stop
docker compose down -v            # Stop and remove volumes
```

### Docker (Service Only)

```bash
docker build -t program-discovery-agent .

docker run -p 8002:8002 \
  -e DB_HOST=mysql-host \
  -e DB_PASSWORD=secret \
  -e OPENAI_API_KEY=sk-... \
  -e INTERNAL_TOKEN_VERIFY_ENABLED=false \
  program-discovery-agent
```

### Service Ports

| Service                 | Port |
| ----------------------- | ---- |
| Program Discovery Agent | 8002 |
| MySQL (Docker)          | 3309 |

---

## Project Structure

```
ouroboros-ai-program-discovery/
├── app/
│   ├── api/                        # Route handlers (thin layer)
│   │   ├── health.py               # GET /health
│   │   ├── institutions.py         # Institution CRUD endpoints
│   │   ├── programs.py             # Program search/ranking endpoints
│   │   ├── chat.py                 # LLM-powered Q&A endpoints
│   │   ├── crawl.py                # Crawl job management
│   │   └── admin.py                # Admin/monitoring endpoints
│   ├── crawlers/                   # Web crawling
│   │   ├── scrapy/
│   │   │   └── spiders/
│   │   │       ├── base_spider.py  # Base spider with helpers
│   │   │       └── university_spider.py  # Configurable spider
│   │   └── crawler_service.py      # Crawl job orchestration
│   ├── llm/                        # LLM integration
│   │   ├── openai_client.py        # OpenAI client with retry
│   │   ├── anthropic_client.py     # Anthropic client with retry
│   │   ├── llm_service.py          # Provider fallback logic
│   │   └── prompts.py              # LLM prompt templates
│   ├── middleware/
│   │   ├── service_auth.py         # Internal JWT validation
│   │   └── logging_middleware.py   # Request logging
│   ├── models/                     # Pydantic schemas
│   │   ├── common.py               # Enums, pagination, responses
│   │   ├── institution.py          # Institution models
│   │   ├── institution_ranking.py  # Ranking models
│   │   ├── program.py              # Program models
│   │   ├── program_requirement.py  # Requirement models
│   │   └── crawl_job.py            # Crawl job models
│   ├── repositories/               # Raw SQL data access
│   │   ├── db_pool.py              # Async MySQL connection pool
│   │   ├── institution_repo.py     # Institution CRUD
│   │   ├── institution_ranking_repo.py
│   │   ├── program_repo.py         # Program CRUD with search
│   │   ├── program_requirement_repo.py
│   │   ├── crawl_job_repo.py
│   │   └── llm_call_log_repo.py    # LLM call logging
│   ├── services/                   # Business logic
│   │   ├── institution_service.py
│   │   ├── program_service.py
│   │   ├── ranking_service.py      # Weighted ranking algorithm
│   │   └── scheduler_service.py    # Placeholder for scheduled crawls
│   ├── core/
│   │   └── logging.py              # structlog configuration
│   ├── utils/
│   │   ├── exceptions.py           # Custom exception hierarchy
│   │   └── trace_id.py             # UUID-v4 trace ID generation
│   ├── config.py                   # Pydantic settings
│   └── main.py                     # FastAPI app with lifespan
├── migrations/                     # SQL migration files (001-006)
├── scripts/
│   ├── run_migrations.py           # Create DB + run all migrations
│   ├── generate_qs_json.py         # Parse QS Excel → JSON
│   ├── seed_qs_rankings.py         # Seed institutions + rankings
│   ├── seed_sample_programs.py     # Seed sample programs
│   ├── seed_singapore_cs_programs.py  # Seed Singapore CS/AI/Data programs (NTU, SMU, SUTD)
│   └── enrich_institutions.py      # Enrich institution data via LLM
├── data/
│   └── qs_world_rankings_2026.json # Generated QS data (1504 universities)
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
├── .github/workflows/
│   └── deploy.yml                  # CI/CD pipeline
├── 2026 QS World University Rankings 1.3 (For qs.com).xlsx  # Source data
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── pytest.ini
├── bandit.yaml
├── .flake8
├── .pylintrc
├── .env.example
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
mysql -h localhost -P ${DOCKER_MYSQL_PORT:-3309} -u root -p -e "SHOW DATABASES;"

# Verify credentials
grep DB_ .env
```

### LLM Calls Failing

**Symptom**: `ValueError: No LLM API keys configured`

```bash
# Verify provider API keys are set
grep API_KEY .env

# Test OpenAI connectivity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### LLM Logs Not Appearing

**Symptom**: `SELECT * FROM llm_call_logs` returns empty

```bash
# Run migrations to create the table
python scripts/run_migrations.py

# Verify table exists
mysql -h localhost -P 3309 -u root -p -e "DESCRIBE llm_call_logs;" ouroboros_program_db

# Make an LLM call to generate logs
curl -X POST http://localhost:8002/chat/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about MIT"}'

# Check logs via API
curl http://localhost:8002/admin/llm/logs \
  -H "Authorization: Bearer <token>"
```

### Monitoring LLM Usage

```bash
# Get recent LLM calls
curl "http://localhost:8002/admin/llm/logs?limit=10" \
  -H "Authorization: Bearer <token>"

# Get usage statistics
curl "http://localhost:8002/admin/llm/stats?days=7" \
  -H "Authorization: Bearer <token>"

# Direct database query for detailed analysis
mysql -h localhost -P 3309 -u root -p ouroboros_program_db \
  -e "SELECT provider, model, COUNT(*) as calls, SUM(input_tokens) as tokens FROM llm_call_logs GROUP BY provider, model;"
```

### Internal Auth Errors

**Symptom**: `401 Unauthorized` on API calls

```bash
# Check if auth is enabled
grep INTERNAL_TOKEN_VERIFY_ENABLED .env

# For local development, disable auth:
echo "INTERNAL_TOKEN_VERIFY_ENABLED=false" >> .env

# For production, ensure public key matches orchestrator
grep INTERNAL_TOKEN_PUBLIC_KEY .env
```

### Seeding Fails

**Symptom**: `FileNotFoundError: data/qs_world_rankings_2026.json`

```bash
# Generate the JSON first
python scripts/generate_qs_json.py

# Then seed
python scripts/seed_qs_rankings.py
```

### Empty Institution Columns

**Symptom**: Many NULL values in `city`, `website_url`, `institution_type`

The QS ranking data doesn't include these fields. Use the enrichment script:

```bash
# Preview changes first
python scripts/enrich_institutions.py --dry-run --limit 5

# Enrich a batch of institutions
python scripts/enrich_institutions.py --limit 100

# Check results
mysql -h localhost -P 3309 -u root -p ouroboros_program_db \
  -e "SELECT name, city, website_url, institution_type FROM institutions WHERE city IS NOT NULL LIMIT 10;"
```

**Note**: Enrichment uses OpenAI API calls, so there's a cost. Use `--limit` to control batch size.

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'app'`

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Port 8002 In Use

```bash
# Find process using port
lsof -i :8002

# Use different port
python -m uvicorn app.main:app --port 8003
```

---

## Integration with Orchestrator

The orchestrator calls Program Discovery Agent for:

1. **Health Probes** — `GET /health`
2. **Program Search** — `GET /programs?field=...&country=...`
3. **Program Ranking** — `POST /programs/rank`
4. **Q&A** — `POST /chat/ask`

### Audience Configuration

```bash
# In orchestrator .env
INTERNAL_TOKEN_AUDIENCE_MAP={"program-discovery":"ouroboros.program-discovery",...}

# In program-discovery .env
INTERNAL_TOKEN_AUDIENCE=ouroboros.program-discovery
```

---

## Attribution

**Developed by**: OuroborosAI Developer Team

**Project**: Ouroboros AI Scholarship Discovery Platform

**Repository**: [github.com/maugus0/ouroboros-ai-program-discovery](https://github.com/maugus0/ouroboros-ai-program-discovery)

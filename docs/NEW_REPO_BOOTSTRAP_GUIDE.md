# New Repository Bootstrap Guide

Practical, incremental path to stand up the greenfield architecture, with teaching notes at each step. Follow phases in order; each phase ends with a stable commit tag so you can revert or branch confidently.

> Mindset: Ship vertical slices early (health -> first metric -> dashboard card) instead of building all plumbing up front.

---

## Phase 0: Create Empty Repository

Goal: Hosted Git repo with only foundation files.

1. Create repo on GitHub (e.g., `capture-intel`). (Private first; open parts later.)
2. Locally:

```
md capture-intel
cd capture-intel
git init
echo # Capture Intelligence Platform> README.md
copy NUL .gitignore
copy NUL LICENSE
git add .
git commit -m "chore: initial empty repo"
git remote add origin <YOUR_REMOTE_URL>
git push -u origin main
```

3. Add **.gitignore** content (Python, Node, env, cache, logs) and choose LICENSE.

Educational Note: Start tiny; resist copying the entire legacy prototype. Each addition should pass a minimal test or command.

---

## Phase 1: Backend Skeleton (FastAPI + Configuration)

Goal: Boot FastAPI with /health endpoint & config validation.

Structure introduced:

```
backend/
  app/
    main.py
    config.py
    routers/health.py
  tests/
    test_health.py
pyproject.toml
Makefile (or tasks.bat)
```

Minimal files:
`pyproject.toml` (excerpt)

```
[project]
name = "capture-intel-api"
version = "0.1.0"
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "pydantic-settings",
  "python-dotenv",
]
```

`backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_env: str = "local"
    api_port: int = 8000
    log_level: str = "INFO"

settings = Settings()  # loads from environment automatically
```

`backend/app/routers/health.py`

```python
from fastapi import APIRouter
router = APIRouter()
@router.get("/health")
def health():
    return {"status": "ok"}
```

`backend/app/main.py`

```python
from fastapi import FastAPI
from .routers import health

app = FastAPI(title="Capture Intelligence API")
app.include_router(health.router)
```

`backend/tests/test_health.py`

```python
from fastapi.testclient import TestClient
from backend.app.main import app

def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

Commands:

```
python -m pip install -e .
uvicorn backend.app.main:app --reload
pytest -q
```

Educational Note: First test creates confidence baseline; every phase keeps tests green.

Tag commit: `git tag v0.1.0-backend-skeleton`.

---

## Phase 2: Database & Migrations

Goal: Introduce PostgreSQL connection + Alembic baseline.

Add deps: `sqlalchemy`, `asyncpg`, `alembic`.

Files:

```
backend/app/db/base.py      # engine/session helper
alembic.ini
backend/app/db/migrations/  # versions/
```

Example engine snippet:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.config import settings

DATABASE_URL = "postgresql+asyncpg://your_username:your_password@localhost:5432/your_database"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

Educational Note: Use **SQLAlchemy Core** for analytics queries later; ORM models only where helpful.

Migration baseline:

```
alembic revision --autogenerate -m "baseline"
alembic upgrade head
```

Tag: `v0.2.0-db-baseline`.

---

## Phase 3: First Domain Slice (Awards Summary)

Goal: Add one real domain endpoint using repository + service layering.

Layers:

```
repositories/awards_repo.py
services/awards_service.py
routers/awards.py
schemas/awards.py
tests/integration/test_awards_summary.py
```

Educational Note: Vertical slice proves architecture. Do not add all endpoints yet.

Repository (Core query pseudo):

```python
AWARDS_SUMMARY_SQL = """
SELECT fiscal_year, SUM(amount) as total
FROM awards
GROUP BY fiscal_year
ORDER BY fiscal_year DESC
LIMIT 5
"""
```

Service composes repository; router returns pydantic response list.

Tag: `v0.3.0-awards-slice`.

---

## Phase 4: Frontend Scaffold (Next.js)

Goal: Basic Next.js app hitting `/health` & `/awards/summary`.

Commands:

```
npx create-next-app@latest web --typescript --eslint --app
cd web
npm install @tanstack/react-query axios
```

Create `web/app/dashboard/page.tsx` with fetch logic & simple chart placeholder.

Educational Note: Keep API base URL configurable via `.env.local`.

Tag: `v0.4.0-frontend-skeleton`.

---

## Phase 5: Observability & Quality Gates

Add: `ruff`, `mypy`, structured logging, request timing middleware, pre-commit hooks.

Makefile targets:

```
lint: ruff check . && mypy backend
fmt: ruff format .
test: pytest -q
```

CI (GitHub Actions): backend lint+test matrix, frontend build, OpenAPI export artifact.

Tag: `v0.5.0-quality-gates`.

---

## Phase 6: Embeddings & Vector Store (Deferred Until Needed)

Introduce `pgvector` or `chromadb` only when a user story requires semantic search. Add feature flag.

Educational Note: Avoid premature complexity; each new system multiplies operational burden.

Tag: `v0.6.0-embeddings` (future).

---

## Phase 7: MCP & AI Layer

Add `ai/` subtree:

```
backend/app/ai/mcp_servers/database/server.py
backend/app/ai/mcp_client_manager.py
```

Expose a single AI-enabled endpoint (e.g., `/awards/analysis`).

Educational Note: Instrument latency + cache responses for repeated prompts.

Tag: `v0.7.0-ai-integration`.

---

## Phase 8: Additional Domains (Projections, Competition, Expiring Contracts)

Repeat vertical slice pattern; add contract tests referencing OpenAPI schema.

Tag: `v0.8.0-expanded-domains`.

---

## Phase 9: Hardening & Split Readiness

Checklist:

- Load testing baseline (k6 or Locust)
- Security headers / rate limiting
- OpenAPI breaking-change guard
- Tool registry hash verification

Tag: `v0.9.0-hardening`.

---

## Phase 10: Pre-Split Review

Decide if splitting repos is justified (use criteria in main structure doc). If yes, extract `api-spec` & `web-app` first.

Tag: `v1.0.0` (GA baseline).

---

## Educational Deep Dives

| Topic                      | Why It Matters                     | Quick Heuristic                                    |
| -------------------------- | ---------------------------------- | -------------------------------------------------- |
| Vertical Slices            | Prevents architecture drift        | Each commit: user-visible or test-visible value    |
| Config Centralization      | Reproducibility & secrets handling | Only import from `config` once per process         |
| SQL in Repos Layer         | Clarity + testability              | Complex query? Give it a name constant + docstring |
| Pydantic Schemas           | Contract stability                 | One response schema per endpoint variant           |
| OpenAPI as Source of Truth | Eliminates drift                   | Generate clients from committed spec artifact      |
| Progressive AI Adoption    | Cost & complexity control          | Add embedding index only when a feature demands it |

---

## Command Cheat Sheet (Windows cmd)

```
REM Run backend
uvicorn backend.app.main:app --reload

REM Run tests
pytest -q

REM Generate Alembic revision
alembic revision --autogenerate -m "feat: awards table"
alembic upgrade head

REM Create Next.js app
npx create-next-app@latest web --typescript --eslint --app

REM Lint & type check
ruff check . && mypy backend
```

---

## Common Pitfalls & Avoidance

| Pitfall                        | Symptom                        | Preventative Action                       |
| ------------------------------ | ------------------------------ | ----------------------------------------- |
| Big-bang import of legacy code | Unclear failures, tangled deps | Re-implement minimal slices incrementally |
| Lack of tests early            | Fear of refactoring            | Add test with each new folder introduced  |
| Bleeding AI features into core | Tight coupling, harder deploys | Keep AI under `ai/` with service facade   |
| Unversioned spec changes       | Frontend breaks unexpectedly   | OpenAPI diff check in CI                  |
| SQL scattered in services      | Duplication & inconsistency    | Single repository module per domain       |

---

## Progress Tracking Template

Use in PR description:

```
Phase: 3 (Awards Slice)
Endpoints Added: /awards/summary
Tests: integration (1), unit (1)
Spec Updated: yes (paths.awards.summary)
Backward Compatible: yes
Risks: none
```

---

## When Something Fails

1. Reproduce locally (run single failing test).
2. Is the failure in infra, logic, or contract? Categorize first.
3. Add a tiny assertion _before_ changing code to lock expected behavior.
4. Fix, re-run full suite, commit.

---

## Exit Criteria for Each Phase

| Phase | Must Be True                                                       |
| ----- | ------------------------------------------------------------------ |
| 1     | /health returns 200; test passes                                   |
| 2     | Alembic upgrade head succeeds; engine connects                     |
| 3     | /awards/summary returns JSON with expected keys; test green        |
| 4     | Dashboard page renders awards summary call; no console errors      |
| 5     | CI passes lint, type, test gates                                   |
| 6     | Vector similarity test returns > threshold score for similar texts |
| 7     | MCP tool call returns table list; AI endpoint responds             |
| 8     | New domain endpoints documented in spec                            |
| 9     | Load test baseline captured & stored                               |
| 10    | Split decision documented (ADR)                                    |

---

## Final Advice

Embrace incrementalism; every commit should either:

1. Add a runnable feature slice, or
2. Improve safety (tests, lint, types), or
3. Reduce future complexity (refactor with tests covering).

If it does none of these, reconsider the change.

---

Happy building! Update this guide as reality diverges—treat it as a living operational playbook.

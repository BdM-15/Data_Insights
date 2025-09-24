# New Greenfield Repository Structure (Proposed)

This structure translates the current prototype (Streamlit + inline SQL) into a production-oriented Next.js + FastAPI architecture with clear separation of concerns, testability, and scalable data/LLM services.

```
root/
├─ README.md                      # High-level overview & quickstart
├─ LICENSE                        # License selection (e.g., Apache-2.0 / Proprietary)
├─ CONTRIBUTING.md                # Conventions & PR process
├─ CODE_OF_CONDUCT.md             # Community standards (optional private; future OSS)
├─ .editorconfig                  # Consistent formatting
├─ .gitignore                     # Base ignore patterns
├─ .env.example                   # Environment variable contract (no secrets)
├─ docker-compose.yml             # Orchestration: api, web, db, vector, ollama
├─ Makefile                       # Common dev targets (setup, lint, test, fmt, run)
├─ pyproject.toml                 # Backend dependencies & tooling (ruff, mypy, pytest)
├─ package.json                   # Frontend dependencies & scripts
├─ pnpm-lock.yaml / package-lock.json
├─ openapi/                       # Generated and hand-authored API specs [POTENTIAL-REPO: api-spec]
│  ├─ openapi.yaml                # Synchronized from backend /docs endpoint
│  └─ fragments/                  # Reusable schema/path partials
├─ infra/                         # Deployment & platform assets [POTENTIAL-REPO: infrastructure]
│  ├─ docker/
│  │  ├─ api.Dockerfile           # FastAPI image
│  │  ├─ web.Dockerfile           # Next.js image
│  │  ├─ worker.Dockerfile        # Background tasks
│  │  └─ vector-init.sql          # pgvector extension init
│  ├─ terraform/                  # (Placeholder) IaC for cloud deployment
│  └─ k8s/                        # (Future) Helm charts
├─ backend/                       # Python domain + API service (can become its own repo) [POTENTIAL-REPO: api-service]
│  ├─ app/
│  │  ├─ ai/                      # AI & MCP integration layer (could split if scaling) [POTENTIAL-REPO: ai-platform]
│  │  │  ├─ mcp_servers/          # Model Context Protocol servers [POTENTIAL-REPO: mcp-servers]
│  │  │  │  ├─ database/
│  │  │  │  │  └─ server.py       # DB tool server (query/list/describe/sample/stats/schema)
│  │  │  │  ├─ web_intel/
│  │  │  │  │  └─ server.py       # (Future) web intelligence scraping tools
│  │  │  │  ├─ document/
│  │  │  │  │  └─ server.py       # (Future) document parsing / summarization tools
│  │  │  │  └─ README.md          # Tool surface & usage (one per server or aggregated)
│  │  │  ├─ mcp_client_manager.py # Client abstraction (discovery, validation, routing)
│  │  │  └─ tool_registry.py      # Optional central registry / dynamic discovery helper
│  │  ├─ main.py                  # FastAPI application factory
│  │  ├─ config.py                # Settings (pydantic BaseSettings)
│  │  ├─ logging.py               # Structured logging config
│  │  ├─ deps.py                  # Dependency injection providers
│  │  ├─ middleware/
│  │  │  ├─ timing.py             # Request timing / correlation IDs
│  │  │  └─ auth.py               # JWT / API key enforcement
│  │  ├─ routers/
│  │  │  ├─ health.py
│  │  │  ├─ auth.py
│  │  │  ├─ filters.py
│  │  │  ├─ awards.py
│  │  │  ├─ agencies.py
│  │  │  ├─ competition.py
│  │  │  ├─ vehicles.py
│  │  │  ├─ geography.py
│  │  │  ├─ projections.py
│  │  │  ├─ expiring.py
│  │  │  ├─ subawards.py
│  │  │  ├─ mentor_protege.py
│  │  │  ├─ embeddings.py
│  │  │  ├─ search.py
│  │  │  ├─ call_plan.py
│  │  │  └─ llm.py
│  │  ├─ schemas/                 # Pydantic response/request models (mirrors OpenAPI)
│  │  ├─ services/                # Business logic modules
│  │  │  ├─ awards_service.py
│  │  │  ├─ competition_service.py
│  │  │  ├─ projection_service.py
│  │  │  ├─ expiring_service.py
│  │  │  ├─ filters_service.py
│  │  │  ├─ llm_summarizer.py
│  │  │  └─ embeddings_service.py
│  │  ├─ repositories/            # Data access (SQLAlchemy Core / text queries)
│  │  │  ├─ awards_repo.py
│  │  │  ├─ competition_repo.py
│  │  │  ├─ projections_repo.py
│  │  │  ├─ expiring_repo.py
│  │  │  ├─ filters_repo.py
│  │  │  ├─ subawards_repo.py
│  │  │  └─ search_repo.py
│  │  ├─ db/
│  │  │  ├─ base.py               # Engine/session setup
│  │  │  ├─ models.py             # Declarative models (minimal; wide tables may stay raw)
│  │  │  ├─ migrations/           # Alembic versions
│  │  │  └─ seed/                 # Seed scripts / demo data
│  │  ├─ tasks/                   # Background / scheduled jobs
│  │  │  ├─ refresh_materialized.py
│  │  │  ├─ reindex_embeddings.py
│  │  │  └─ ingest_mentor_protege.py
│  │  └─ utils/
│  │     ├─ time.py
│  │     ├─ security.py
│  │     ├─ pagination.py
│  │     └─ vector.py
│  ├─ tests/                      # Co-located tests (may remain or migrate to each service repo)
│  │  ├─ conftest.py
│  │  ├─ integration/
│  │  │  ├─ test_awards_endpoints.py
│  │  │  ├─ test_competition_endpoints.py
│  │  │  ├─ test_embeddings_search.py
│  │  │  └─ test_projections.py
│  │  ├─ unit/
│  │  │  ├─ test_awards_service.py
│  │  │  ├─ test_projection_math.py
│  │  │  └─ test_vector_similarity.py
│  │  └─ performance/
│  │     └─ test_latency_smoke.py
│  └─ scripts/
│     ├─ export_openapi.sh        # Pull live spec to openapi/openapi.yaml
│     ├─ create_demo_dataset.py
│     └─ backfill_embeddings.py
├─ frontend/                      # Next.js UI [POTENTIAL-REPO: web-app]
│  ├─ next.config.mjs
│  ├─ tsconfig.json
│  ├─ app/                        # Next.js App Router
│  │  ├─ layout.tsx
│  │  ├─ page.tsx                 # Default dashboard redirect
│  │  ├─ dashboard/
│  │  │  ├─ page.tsx              # Strategic default dashboard
│  │  │  ├─ components/
│  │  │  │  ├─ MetricCards.tsx
│  │  │  │  ├─ AgencyTreemap.tsx
│  │  │  │  ├─ QuarterlyTrends.tsx
│  │  │  │  ├─ VehiclePreferences.tsx
│  │  │  │  ├─ GeographyMap.tsx
│  │  │  │  ├─ ExpiringContracts.tsx
│  │  │  │  └─ ProjectionChart.tsx
│  │  ├─ capability-stances/
│  │  │  └─ page.tsx
│  │  ├─ competition/
│  │  │  └─ page.tsx
│  │  ├─ search/
│  │  │  └─ page.tsx              # Structured + semantic search UI
│  │  ├─ call-plan/
│  │  │  └─ page.tsx
│  │  └─ api/                     # Edge helper routes (client facade if needed)
│  ├─ lib/
│  │  ├─ apiClient.ts             # Axios/Fetch wrapper with auth & retry
│  │  ├─ queryKeys.ts             # React Query keys
│  │  ├─ formatters.ts
│  │  ├─ chartTheme.ts
│  │  └─ constants.ts
│  ├─ components/
│  │  ├─ layout/
│  │  │  ├─ Sidebar.tsx
│  │  │  ├─ TopNav.tsx
│  │  │  └─ FilterDrawer.tsx
│  │  ├─ forms/
│  │  │  └─ DateRangePicker.tsx
│  │  ├─ shared/
│  │  │  ├─ LoadingState.tsx
│  │  │  ├─ ErrorBoundary.tsx
│  │  │  └─ DataTable.tsx
│  ├─ hooks/
│  │  ├─ useFilters.ts
│  │  ├─ useAwardSummary.ts
│  │  ├─ useQuarterlyTrends.ts
│  │  ├─ useCompetitionTreemap.ts
│  │  └─ useProjection.ts
│  ├─ styles/
│  │  ├─ globals.css
│  │  ├─ variables.css
│  ├─ tests/
│  │  ├─ unit/
│  │  │  ├─ formatters.test.ts
│  │  ├─ integration/
│  │  │  ├─ dashboard.test.tsx
│  │  └─ e2e/
│  │     ├─ dashboard.spec.ts     # Playwright / Cypress
│  └─ public/
│     ├─ favicon.ico
│     └─ logo.svg
├─ data/                          # Sample & seed data [POTENTIAL-REPO: sample-data]
│  ├─ samples/
│  │  ├─ prime_awards_sample.parquet
│  │  └─ subawards_sample.parquet
│  └─ seeds/                      # SQL/CSV for initial local population
├─ embeddings/                    # Model artifacts / vector cache [POTENTIAL-REPO: model-artifacts]
│  ├─ models/                     # (Optional) local GGUF or ONNX models
│  └─ cache/                      # Vector store warm cache artifacts (gitignored)
├─ docs/                          # Documentation hub (could become a docs site) [POTENTIAL-REPO: docs-site]
│  ├─ PRD.md
│  ├─ TECHNICAL_COMPANION.md
│  ├─ CAPTUREINTEL.md
│  ├─ OPENAPI_SKELETON.yaml
│  ├─ SCHEMA_DATA_DICTIONARY.md   # Machine readable (optional) JSON/YAML version later
│  ├─ SQL_VISUALIZATION_QUERIES.md
│  ├─ ARCHITECTURE_DECISIONS/
│  │  └─ ADR-0001-initial-architecture.md
│  └─ SECURITY_POSTURE.md         # RBAC, data handling, logging redaction
├─ scripts/                       # Dev/ops helper scripts (could move to devtools repo) [POTENTIAL-REPO: dev-tools]
│  ├─ dev_up.sh                   # Compose up + wait-for
│  ├─ recreate_db.sh
│  ├─ format_all.sh
│  └─ ci_lint.sh
├─ .github/                       # CI/CD workflows (optionally centralize) [POTENTIAL-REPO: shared-ci]
│  ├─ workflows/
│  │  ├─ backend-ci.yml           # lint, typecheck, test, build image
│  │  ├─ frontend-ci.yml          # lint, typecheck, test
│  │  ├─ nightly-materialized-refresh.yml
│  │  └─ release-draft.yml
│  ├─ ISSUE_TEMPLATE/
│  │  ├─ feature_request.md
│  │  ├─ bug_report.md
│  │  └─ data_change.md
│  └─ dependabot.yml
└─ SECURITY.md                    # Vulnerability disclosure
```

## Environment Variables (.env.example)

```
API_ENV=local
API_PORT=8000
DB_HOST=postgres
DB_PORT=5432
DB_NAME=capture_intel
DB_USER=app_user
DB_PASSWORD=change_me
DB_POOL_SIZE=10
EMBEDDING_MODEL=all-minilm-l6-v2
VECTOR_DIM=384
JWT_SECRET=change_me
JWT_EXP_MINUTES=60
LOG_LEVEL=INFO
ENABLE_METRICS=true
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=mistral:7b
ALLOW_ORIGINS=*
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT_PER_MIN=120
```

## Initial Makefile Targets

```
setup: install-backend install-frontend
install-backend:
	pip install -e .
install-frontend:
	cd frontend && npm install
up:
	docker compose up -d --build
lint:
	ruff check . && mypy backend
fmt:
	ruff format .
test:
	pytest -q
spec-export:
	bash backend/scripts/export_openapi.sh
```

## Implementation Notes

- Repositories own SQL (text + parameterization) referencing the canonical SQL catalog.
- Services compose repositories + domain logic (projection math, market share computation, semantic enrichment triggers).
- Routers remain thin (validation + orchestration + response mapping).
- Embedding workflow: repository batch select -> service vectorize -> repository upsert.
- Future: event bus or lightweight task queue (e.g., Dramatiq / Celery) can replace cron-like task scripts.

### MCP (Model Context Protocol) Integration

Location in this structure:

```
backend/
	app/
		ai/
			mcp_servers/
				database/
					server.py                # Database tool server (query/list/describe/sample/stats/schema)
				web_intel/
					server.py                # (Optional future) Web intelligence scraping tools
				document/
					server.py                # (Optional future) Document parsing/summary tools
				README.md                  # Per-server usage & tool contract (one README per folder or aggregated)
			mcp_client_manager.py        # Client abstraction (discovery, validation, routing)
			tool_registry.py             # Central mapping (if multiple servers) or dynamic discovery helper
```

Rationale:

- Keeps AI-related orchestration separate from pure business services.
- Mirrors current prototype path (`src/backend/ai/mcp_servers`) for easier migration.
- Allows future servers (web_intel, document_editor, visualization_assist, analysis_reasoner) without cluttering core `routers/`.
- Encourages clear tool surface documentation (each server folder self-contained).

Lifecycle Pattern:

1. FastAPI startup event imports `ai.mcp_client_manager` (lazy initialize on first tool call to keep cold start low).
2. Client manager discovers server scripts (explicit allow‑list) and registers tools.
3. Routers/services request tools through the manager (no direct subprocess handling in endpoint code).
4. Add tests under `backend/tests/integration/test_mcp_database.py` exercising tool round‑trips.

Security / Ops Notes:

- Enforce allow‑listed executable paths to avoid arbitrary script execution.
- Wrap tool calls with timeout & circuit breaker (simple retry/backoff decorator in `utils/` if needed).
- Log tool latency + success/failure for observability.

Future Extensions:

- SSE or WebSocket transport for streaming outputs (align with FastMCP capabilities).
- Tool auth gating (capabilities map) once multi-tenant or role-based access is introduced.

### Why "Greenfield"?

"Greenfield" denotes a fresh architectural rebuild rather than incremental refactoring of the current Streamlit prototype. It signals:

- Freedom to realign folder boundaries to domain-driven slices.
- Adoption of production patterns (API-first FastAPI + Next.js separation, CI pipelines, strict typing, ADRs).
- Avoiding legacy coupling (ad hoc SQL in UI) by enforcing repository/service/endpoint layering from day one.
- Clear migration phase: old repo = reference; new repo = authoritative implementation.

If preferred, rename this file later to `REPO_STRUCTURE.md` once the scaffold is initialized and "greenfield" context is implicit.

## Next Steps After Scaffold

1. Generate FastAPI project with Pydantic models mirroring OpenAPI skeleton.
2. Implement repository layer using SQLAlchemy Core (avoid ORM overhead for wide analytic tables).
3. Add Alembic baseline migration (extensions: pgvector; schemas s1_raw/s2_interim/s3_processed if reproduced).
4. Implement /health, /metadata/version, /awards/summary endpoints first (smoke path).
5. Integrate React Query + initial dashboard metrics cards hitting new API.
6. Add observability (structlog + OpenTelemetry trace IDs propagation) early.
7. Backfill semantic vector store and validate /embeddings/query.

This file is a living artifact—update alongside ADRs as decisions evolve.

## Future Repository Extraction Strategy

The current mono-repo style scaffold is optimized for velocity. As the platform matures, the labeled [POTENTIAL-REPO:*] areas can be split along these boundaries:

| Candidate       | Primary Responsibility                    | Split Trigger                                   | Interface Contract                                 | Risks if Delayed                      | Prep Actions Now                                         |
| --------------- | ----------------------------------------- | ----------------------------------------------- | -------------------------------------------------- | ------------------------------------- | -------------------------------------------------------- |
| api-spec        | Single source of OpenAPI truth            | Multiple language clients; versioned public API | Versioned OpenAPI docs, changelog                  | Spec drift across services            | Keep spec generation deterministic; add diff check in CI |
| infrastructure  | Infra as code, Docker/K8s, Terraform      | Separate platform team; multi-env deployments   | Image tags, Helm chart values, Terraform modules   | Tight coupling slows infra changes    | Isolate compose overrides; parameterize infra scripts    |
| api-service     | Core FastAPI business APIs                | Independent scaling / deployment cadence        | REST/JSON, pagination, auth tokens                 | Hard to enforce SLAs                  | Keep clean service boundary, avoid UI imports            |
| ai-platform     | LLM orchestration, embeddings, MCP client | Divergent model lifecycle vs API releases       | gRPC/WebSocket or internal REST; vector search API | Model changes force full deploys      | Abstract AI calls behind service interfaces              |
| mcp-servers     | Tool servers (db, web, doc)               | Need separate runtime security hardening        | Std I/O or SSE tool protocol                       | Tool outages impact main API          | Standardize tool health pings                            |
| web-app         | Frontend Next.js UI                       | Independent release cadence, CDN deployment     | REST/GraphQL API + ENV config                      | UI deploy blocked by backend pipeline | Enforce API client generated from spec                   |
| sample-data     | Reusable anonymized datasets              | Shared usage across demos/tests                 | Versioned artifacts, checksum                      | Data bloat in main repo               | Store large files via Git LFS                            |
| model-artifacts | GGUF/ONNX models, embeddings              | Larger model storage, licensing separation      | Model registry references                          | Repo size growth, slow clone          | Use hashed filenames + manifest                          |
| docs-site       | Developer & user docs                     | Public documentation site build                 | Static site (MkDocs/Docusaurus)                    | Docs lag platform features            | Structure docs by domain now                             |
| dev-tools       | Scripts, local automation                 | Cross-repo reuse; internal CLI                  | CLI semantics/versioning                           | Script duplication & drift            | Wrap scripts in a `di` CLI early                         |
| shared-ci       | Centralized workflows                     | >3 repos with duplicated CI logic               | Reusable workflow templates                        | CI divergence, security gaps          | Parameterize current workflows                           |

### Extraction Phases (Recommended)

1. Stabilize API domain models & pagination/auth patterns (Weeks 1-2).
2. Externalize OpenAPI spec & generated clients (Week 3) – create `api-spec` repo.
3. Split `web-app` for independent deployment (Weeks 4-5) once contract tests pass.
4. Carve out `ai-platform` + `mcp-servers` (Weeks 6-7) behind internal service endpoints.
5. Move infra to dedicated repo with pipeline templates (Week 8).
6. Optional: materialize `docs-site` for public/internal portal (Week 9+).

### Contract Enforcement Mechanisms

- Consumer-driven contract tests (frontend -> API; AI service -> API) run in PR CI.
- OpenAPI diff gate: failing build if breaking changes without version bump.
- Semantic versioning for spec + AI tool schemas.
- Tool registry manifest (YAML) hashed & validated at startup.

### Monorepo Retention Criteria

Keep combined until at least two of these are true:

- Independent scaling requirements emerge (API vs AI embeddings).
- Distinct deploy cadences (frontend daily, backend weekly).
- Compliance boundary (model artifacts licensing separation).
- Team ownership splits (dedicated platform/AI vs product teams).

### Preparation Checklist (Do Now)

- [ ] Add OpenAPI generation CI job producing artifact & diff.
- [ ] Introduce a `clients/` folder for generated SDKs (to relocate later).
- [ ] Create `tool_registry.yaml` describing MCP tools (name, I/O schema, owner).
- [ ] Tag Docker images with git SHA + semver for traceability.
- [ ] Add contract tests scaffolds in `backend/tests/integration/` referencing spec.
- [ ] Document versioning policy in `docs/ARCHITECTURE_DECISIONS/ADR-0002-versioning.md`.

### Naming Guidance

| Current Path   | Future Repo Name    | Reason                         |
| -------------- | ------------------- | ------------------------------ |
| backend/app    | capture-intel-api   | Clear domain + API focus       |
| backend/app/ai | capture-intel-ai    | Separates model/tool lifecycle |
| frontend       | capture-intel-web   | User-facing assets             |
| openapi        | capture-intel-spec  | Contract-first distribution    |
| infra          | capture-intel-infra | Deployment & platform          |

Revisit boundaries quarterly; record changes via ADRs.

# PRD: Data Insights Capture Management App

## 1. Product overview

### 1.1 Document title and version

- PRD: Data Insights Capture Management App
- Version: 0.2 (Refined – August 15, 2025)

### 1.2 Product summary

The application empowers a capture manager to rapidly understand historical federal contract spending patterns, evaluate competitive position, identify and qualify future opportunities, and generate structured capture profiles and win themes. It unifies processed USAspending.gov prime/subaward data with (future) SAM.gov opportunity intelligence, exposing curated analytical views, an advanced opportunity explorer, a structured capability stance module, and a free‑form AI data agent for exploratory questioning and artifact generation.

The MVP focuses on a single internal user (you) acting in the capture manager role. Emphasis is on local processing (privacy), performant materialized-view powered analytics, maintainable modular code, and Markdown-first export pathways to later DOCX/PDF. Complexity is intentionally constrained: no multi-user authentication, no external SaaS dependencies, and a lean, opinionated UI enabling fast situational awareness and decision support.

## 2. Goals

### 2.1 Business goals

- Accelerate capture analysis cycle time (historical -> opportunity framing) by >60% vs manual spreadsheets.
- Improve early bid/no-bid decision confidence via structured capability gap and competitor insight outputs.
- Provide foundation for AI-assisted narrative generation (win themes, strategic positioning) entirely on local infrastructure.
- Establish a scalable, modular data + AI architecture for future multi-user / external data source expansion.
- Reduce maintenance friction through clear separation of extract–transform–load (ETL), analytics, UI, AI agent, and export concerns.

### 2.2 User goals

- Quickly filter and visualize spend trends (by agency, North American Industry Classification System (NAICS), Product Service Code (PSC), contractor) within <5 seconds.
- Identify expiring contracts and potential recompetes with enough lead time for pursuit planning.
- Explore opportunities (historical + future) with advanced faceted, semantic, and pattern-based search.
- Generate a capability stance baseline to compare internal strengths against customer needs and competitors.
- Interactively ask natural language questions of the dataset and receive accurate, source-linked answers.
- Export a draft capture profile (Markdown) containing structured sections and AI-suggested win themes.

### 2.3 Non-goals

- Multi-user authentication / Role-Based Access Control (RBAC) (deferred).
- Real-time streaming analytics or sub-second updates (batch + on-demand only).
- Full proposal automation / pricing models.
- Integration with proprietary external paid platforms (GovWin IQ, Bloomberg Government) in MVP.
- Complex workflow management or pursuit pipeline CRM features.
- Full document generation to DOCX/PDF (post-MVP; only Markdown now).

### 2.4 Technology stack (MVP & near-term)

| Layer                   | Selection                                                           | Purpose / Scope                                                            | Key Notes                                                                                                          |
| ----------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Frontend UI             | Next.js (React 18 + TypeScript)                                     | Modular dashboard, explorer, capability & uplift simulator views           | Component library (MUI or Chakra TBD), AG Grid / MUI Data Grid, design tokens, SSR/ISR                             |
| Visualization           | ECharts, Plotly, (Altair for spec prototyping), Matplotlib (static) | Interactive & high‑performance charts, exploratory graphics, export images | ECharts for perf & theming, Plotly for ad-hoc rich interactivity, Altair to iterate specs, Matplotlib fallback PNG |
| Backend API / Services  | FastAPI (planned lightweight endpoints)                             | Programmatic access (future multi-user, agents), background tasks          | Phase-in after core dashboards stable; internal module calls first                                                 |
| Data Access / ORM       | SQLAlchemy + SQLModel                                               | Connection management, typed models, query composition                     | Direct SQL for heavy analytic/materialized view queries                                                            |
| Database                | PostgreSQL 15+                                                      | Primary OLAP-ish store (star/flat processed views)                         | Schemas: s1_raw, s2_interim, s3_processed; Extensions: pgvector, pg_trgm (candidate)                               |
| Vector / Semantic       | pgvector (in-DB)                                                    | Embedding storage & similarity search                                      | Index: ivfflat w/ appropriate lists; alt: HNSW (future)                                                            |
| Local LLM Runtime       | Ollama                                                              | Runs base + adapter (LoRA) models locally                                  | Models: llama3-8b, mistral-7b, phi-3-mini; adapter selection via config                                            |
| PEFT / Training         | PEFT (LoRA, QLoRA) + bitsandbytes                                   | Parameter-efficient fine-tuning                                            | Off-line GPU sessions; artifacts versioned in models/                                                              |
| Retrieval Layer         | Direct SQL + profile/materialized views + embedding kNN             | Hybrid structured + semantic retrieval                                     | Later: lightweight feature store or caching layer                                                                  |
| Orchestration (Agents)  | Model Context Protocol (MCP)                                        | Tool registry, enrichment tasks, AI agent tool invocation                  | Task registry JSON used pre-scheduler                                                                              |
| Scheduling (Future)     | APScheduler or Prefect (TBD)                                        | Timed refresh jobs, enrichment cycles                                      | MVP: manual triggers + simple scripts                                                                              |
| Logging & Observability | Python logging + structured JSON + dashboard panel                  | Query perf, AI interactions, enrichment metrics                            | Potential future OpenTelemetry integration (local only)                                                            |
| Testing                 | Pytest + hypothesis (selected cases)                                | Unit, integration, property-based tests                                    | Performance smoke tests for key queries                                                                            |
| Data Processing         | Pandas, Polars (exploratory candidate)                              | Transform & feature engineering                                            | Polars considered if Pandas bottlenecks appear                                                                     |
| Packaging & Env         | requirements.txt + virtualenv                                       | Dependency pin + reproducibility                                           | Later: Dockerfile + docker-compose.yml (post MVP)                                                                  |
| Config Management       | python-dotenv via config.py                                         | Centralized validated configuration                                        | All env access funneled through config module                                                                      |
| Security / Privacy      | Local-only runtime, no outbound AI calls                            | Data governance                                                            | Future: SBOM + dependency scan                                                                                     |
| Documentation           | Markdown (docs/), Mermaid diagrams                                  | Architecture & process transparency                                        | Auto-gen schema docs (future script)                                                                               |

Selection criteria: local execution performance, simplicity, ecosystem maturity, minimal external dependencies (privacy), extensibility for multi-user future.

Performance targets align with hardware: 64 Gigabytes (GB) Random Access Memory (RAM), NVIDIA RTX 4060 (8 Gigabytes (GB) Video Random Access Memory (VRAM)).

## 3. User personas

### 3.1 Key user types

- Capture Manager (sole MVP persona)

### 3.2 Basic persona details

- **Capture Manager**: Strategically evaluates historical spend, competitor behavior, and alignment of internal capabilities to shape win strategy and pursue high-probability opportunities efficiently.

### 3.3 Role-based access

- **Capture Manager**: Full read/write (local) access to data processing, analytics views, Artificial Intelligence (AI) agent, capability stance editing, and exports. (No differentiated permissions in MVP.)

## 4. Functional requirements

This section summarizes feature domains; detailed, testable specifications are defined in Section 10 (User stories). Redundant descriptive bullets from earlier drafts have been collapsed to reduce duplication.

| Domain / Feature Group                                                              | Priority   | Outcome (summary)                                                 | User Story Range                       |
| ----------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------- | -------------------------------------- |
| Strategic dashboard (market, future opps, agency, competition, vehicles, geography) | High / Med | Fast situational awareness across core procurement dimensions     | GH-001..GH-015                         |
| Opportunity explorer (faceted + semantic)                                           | High       | Powerful multi-filter & similarity search + saved views           | GH-016..GH-019                         |
| Capability stance & gaps                                                            | High       | Internal vs competitor capability mapping & gap surfacing         | GH-020..GH-022, GH-048                 |
| AI data agent & narratives                                                          | High       | Natural language Q&A & narrative generation with provenance       | GH-023..GH-027, GH-057..GH-066, GH-090 |
| Capture profile export                                                              | High       | Structured Markdown export with AI sections & actions             | GH-028, GH-029, GH-055                 |
| Data ingestion & refresh                                                            | Medium     | Incremental USAspending + SAM.gov stub & dedup                    | GH-030, GH-031                         |
| Performance & diagnostics                                                           | High       | Latency transparency, refresh control, guardrails                 | GH-032, GH-033, GH-050                 |
| Configuration & privacy                                                             | High       | Central config, local-only enforcement, privacy badge             | GH-034, GH-035, GH-047                 |
| Logging & observability                                                             | High       | Full provenance & action logging                                  | GH-039, GH-040, GH-045                 |
| Win probability & uplift modeling                                                   | Medium     | Heuristic probability & action uplift recommendations             | GH-051..GH-056                         |
| Data enrichment & knowledge layer                                                   | High       | Enriched entities, embeddings, profiles, graph & drift monitoring | GH-067..GH-090                         |
| Modernization & dependency consolidation                                            | Medium     | Lean footprint & upgrade readiness                                | GH-106..GH-110                         |
| Frontend foundation (Next.js)                                                       | High       | Scalable UI shell, API contract validation, component decisions   | GH-111..GH-115                         |

Non-functional attributes (performance, reliability, security, maintainability) are cataloged in Section 17 and linked from acceptance criteria (Section 15).

## 5. User experience

### 5.1 Entry points & first-time user flow

- Launch app -> Strategic Dashboard default (Market Overview tab) with default NAICS (561210) and last 6 fiscal years.
- Contextual tooltips explaining each metric card & chart.
- Sidebar filters persist across tabs (session state) with live reload button.
- First export triggers explanatory modal about structure & AI sections.

### 5.2 Core experience

- **Filter–analyze loop**: Adjust filters -> load under 5s -> interpret metrics -> pivot to competitor or opportunity dimension.
  - Ensures rapid hypothesis testing.
- **Explore–narrate**: Use AI agent to convert analytic findings into draft narrative blocks.
  - Reduces manual synthesis time.
- **Capability alignment**: Map internal vs competitor vs customer signals to support bid/no-bid decision.
  - Increases strategic clarity.

### 5.3 Advanced features & edge cases

- Semantic search fallback if vector column absent.
- Graceful empty states (no data -> explanation + suggestion to relax filters).
- Large query guardrails (hard row cap with “refine filters” prompt).
- Projection logic omits quarters already elapsed in current Fiscal Year (FY).

### 5.4 UI/UX highlights

- Consistent theming via centralized theme + CSS generator.
- Materialized view powered metrics labeled with “(cached)” badges.
- Inline provenance icons linking to source (view/table name) for trust.
- Export preview panel before save.

## 6. Narrative

A capture manager opens the Strategic Dashboard, applies agency and NAICS filters, and instantly sees obligation trends, top competitors, and expiring contracts. Pivoting to the Capability Stance module, they highlight internal differentiators against inferred competitor capabilities. They invoke the AI data agent asking for “win themes for Agency X’s expiring facilities support contracts,” receiving a structured draft with source-linked metrics. Satisfied, they export a capture profile Markdown file containing narratives, competitive positioning, and recommended actions—dramatically reducing manual analysis time.

## 7. Success metrics

To avoid redundancy with Non-functional Requirements (Section 17) and Acceptance & release criteria (Section 15), this section lists high-level outcome metrics only; detailed performance / quality thresholds live in those sections.

### 7.1 User-centric metrics

- Median dashboard load (filtered) ≤ 5s.
- Time to produce a first draft capture profile ≤ 30 minutes (baseline > 90 minutes).
- ≥ 80% of AI-generated win themes accepted or lightly edited.
- < 10% of AI agent queries require rephrase due to misunderstanding.

### 7.2 Business metrics

- 60% reduction in manual data wrangling time.
- Increased qualified opportunity pipeline quality (subjective scoring) after using capability stance.
- Reuse rate of saved opportunity explorer queries (>30% of sessions).

### 7.3 Technical metrics (selected – see Section 17 for full NFRs)

- Materialized view query latency meets Section 17.1 thresholds.
- Monthly data refresh completes within defined performance envelope (Section 17.1).
- Local-only AI inference compliance (verified per Section 17.5).

## 8. Technical considerations

### 8.1 Integration points

- PostgreSQL schemas: `s1_raw` (ingest), `s2_interim` (dedup/enrichment), `s3_processed` (analytics + materialized views).
- AI inference: Ollama local models (llama3 / mistral / phi variants) via internal wrapper.
- Future: SAM.gov daily ingestion stub (scheduled script) -> `s2_interim.sam_opportunities` -> processed view.

### 8.2 Data storage & privacy

- All data & embeddings local; no PII expansion beyond source fields.
- Logging tables (`app_logs.*`) store prompts, tool metadata, structured reasoning JSON.
- Capability stance & generated narratives stored locally (table or JSON file under versioning).

### 8.3 Scalability & performance

- Heavy aggregation pushed into materialized views with manual refresh triggers (future incremental refresh scheduling).
- Index coverage across frequent filter dimensions (already extensive in `s3_processed.usaspending_prime_awards`).
- Potential future partitioning by fiscal year for large scale.

### 8.4 Potential challenges

- Semantic description / vector embeddings pipeline not fully populated (risk to AI search quality).
- Schema drift from source (new columns) requiring dynamic schema alteration (handled by utility but needs monitoring).
- Projection modeling assumptions (2% escalation, even distribution) may need calibration; document clearly.
- Overfitting win themes to historical language vs customer current intent.

### 8.5 Technology stack detail & rationale

| Aspect                        | Rationale                                      | Risks                                                 | Mitigations                                                                                |
| ----------------------------- | ---------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Next.js + TypeScript baseline | Rich component ecosystem, SSR/ISR flexibility  | Higher initial setup complexity                       | Scaffold reusable modules, strict lint/type rules, story-driven component dev              |
| PostgreSQL single store       | Simplifies ops, strong indexing + extensions   | Heavy analytical workloads may strain single instance | Materialized views, indexes, consider read replica/partitioning future                     |
| pgvector in-DB                | Unified transactional + vector operations      | Potential slower vs specialized ANN engine at scale   | Use ivfflat index, monitor latency; switch to standalone (e.g., Qdrant) if corpus explodes |
| Ollama local models           | Privacy, offline reproducibility               | Lower base capability vs large hosted models          | Retrieval augmentation + targeted fine-tuning adapters                                     |
| PEFT (LoRA/QLoRA)             | Low VRAM footprint adaptation                  | Possible underfitting for niche tasks                 | Multi-intent adapters, style tokens                                                        |
| Direct SQL for heavy queries  | Predictable performance tuning & explain plans | More boilerplate vs ORM                               | Hybrid: ORM for CRUD, raw SQL for analytics                                                |
| Materialized views            | Fast dashboard load times                      | Staleness windows                                     | Manual refresh triggers + future incremental scheduling                                    |
| MCP orchestration             | Standardizes tool invocation                   | Added initial complexity                              | Start with minimal registry + expand                                                       |
| Pandas primary                | Familiar & flexible                            | Memory overhead for very large frames                 | Chunked processing, consider Polars for outliers                                           |
| Plotly + Altair               | Balance of interactivity & declarative style   | Duplicate functionality overhead                      | Guidelines for usage (Plotly interactive; Altair declarative summary)                      |
| Single-process MVP            | Simplicity                                     | Limited concurrency                                   | Introduce FastAPI + async for heavy concurrent agent queries later                         |
| requirements.txt pinning      | Predictable builds                             | Dependency drift                                      | Monthly review & renovate script (future)                                                  |

Version pin strategy: Pin major + minor for core libs (FastAPI, SQLAlchemy, pandas), flexible patch updates. Maintain `requirements.lock` (future) and vulnerability scan script (post-MVP task).

Adoption checkpoints: (a) Baseline dashboards fast (<5s) on materialized views; (b) Embedding similarity queries <300 milliseconds p95; (c) Adapter model latency <= +10% vs base.

### 8.6 Runtime, language & hardware baseline

**Language & Version**

- Python 3.12.x (confirmed via compiled artifacts) – chosen for performance improvements (faster CPython interpreter, better typing) and broad ecosystem support.

**Environment Management**

- Virtual environment (`insight_venv/`) with pinned `requirements.txt`.
- Future: generate `requirements.lock` (hashes) and optional Docker image (post-MVP) for reproducibility.
- All configuration centralized in `config.py` with `.env` file (never commit secrets).

**Library & Tool Grouping (Python + Frontend)**

- Core Web / API (Python): fastapi, uvicorn, httpx.
- Frontend (Node/JS project – separate `package.json`): next, react, react-dom, typescript, @tanstack/react-query, (mui/material OR @chakra-ui/react), ag-grid-react / @mui/x-data-grid, echarts-for-react, react-hook-form, zod, testing-library, jest, playwright (E2E), axe-core (a11y).
- Visualization (Python support / server pre-processing): altair (spec prototyping), plotly (JSON configs), matplotlib (static image export). (ECharts/Plotly rendered client-side in Next.js.)
- Data Processing & Compute: pandas, numpy, pyarrow, tqdm, narwhals (compat), Polars (candidate – not yet pinned), SQLAlchemy, asyncpg, psycopg2-binary.
- ML / AI / LLM: ollama (client), sentence-transformers (embeddings), langchain-core (templating – deferred), langgraph (agent workflows upcoming – deferred), PEFT related (LoRA via PEFT planned), bitsandbytes (implied for QLoRA – to be added when GPU fine-tune stage begins).
- Orchestration / Protocol: mcp (Model Context Protocol implementation).
- Validation & Schema: pydantic, annotated-types, jsonschema.
- Logging & Observability: (baseline python logging), blinker (signals), langfuse (telemetry/analytics – deferred), tenacity (retry), watchdog (file watching for hot reload).
- Utilities & Packaging: python-dotenv, requests, packaging.
- Visualization Low-level Support (Python): contourpy, kiwisolver, pillow, fonttools, protobuf.
- Performance / Async: anyio, sniffio, h11.
- Testing (Python): pytest (planned), hypothesis (planned), property-based tests hooking into core transforms.

**Planned Additions (not yet in list)**

- bitsandbytes (GPU quantization) – gated by adapter training start.
- peft – if not implicitly pulled via pydantic-ai or future training script.
- faiss / ann-lite alternative ONLY if pgvector performance proves insufficient (>500 ms p95 at scale).
- polars – add once memory or latency profiling flags Pandas bottlenecks (document in CHANGELOG when introduced).

**Hardware Baseline**

- CPU: Multi-core x86_64 (>=8 physical cores recommended) – leverage parallelization for ETL and embedding generation batches.
- RAM: 64 Gigabytes (GB) system memory – enables in-memory DataFrame operations on moderate USAspending slices without spilling.
- GPU: NVIDIA GeForce RTX 4060 (8 Gigabytes (GB) Video Random Access Memory (VRAM)) – suitable for inference of 7B–13B models (quantized) and LoRA adapter training with QLoRA.
- Storage: NVMe SSD recommended (sequential read >2.5 GB/s) for faster initial load of embeddings / dataset shards.
- CUDA Toolkit: 12.x compatible drivers (ensure alignment with bitsandbytes compiled binaries when introduced).
- Compute Capability: 8.9 (Ada Lovelace) – supports bfloat16, enabling mixed precision benefits.

**Performance / Capacity Targets (Hardware-Aware)**

- Inference latency (tuned 7B model, 512 output tokens): p95 ≤ 2.5 seconds.
- Embedding batch throughput (sentence-transformers small model, 512 token average): ≥ 1,200 records/minute on GPU; scale back-off strategy: dynamic batching size (8–32) based on VRAM telemetry.
- Materialized view refresh (core analytics views): < 90 seconds for baseline dataset (post indexes).
- Incremental enrichment job (≤5% changed rows): completes within 10 minutes from detection.

**Tooling & Scripts (Planned)**

- `scripts/profile_embeddings.py` – measures embedding latency & drift.
- `scripts/benchmark_queries.py` – records p50/p95 for key SQL queries; outputs JSON.
- `scripts/generate_instruction_data.py` – builds instruction tuning dataset from dashboard queries + dictionary.

**Operational Guidelines**

- Re-run benchmark suite after dependency upgrades or adapter deployment; store results under `benchmarks/` with timestamp.
- Avoid upgrading major model runtime (Ollama version) concurrently with adapter release – stagger to isolate regressions.
- Enforce minimum free VRAM threshold (~1.5 Gigabytes (GB)) before launching training or large embedding batches to prevent OOM.

**Degradation Strategies**

- If GPU unavailable: fallback to CPU inference for critical short responses (<256 tokens) and restrict narrative generation length; warn via diagnostics panel.
- If memory pressure detected (>85% RAM): switch DataFrame operations to chunked mode; optional on-disk Arrow spill (future enhancement).

**Success Indicators**

- Reproducible environment rebuild time < 10 minutes (fresh clone -> functional dashboard).
- Zero GPU OOM incidents across a week of typical usage (tracked in logs).
- Library vulnerability scan (future) shows 0 critical outstanding CVEs.

### 8.7 Modernization & Python 3.14 readiness / dependency consolidation

**Forward-looking Python Upgrade (3.12 -> 3.14)**

- Target evaluation window: within 60 days of Python 3.14 stable release.
- Expected benefits (monitor PEP implementations): incremental interpreter speedups, potential improved free-threading experiments (if stabilized), enhanced f-string & typing features reducing boilerplate.
- Compatibility guardrails: avoid use of deprecated 3.12 APIs marked for removal in 3.14 (periodic `python -Wd` runs). Maintain CI matrix (future) 3.12 + provisional 3.14.
- Migration strategy: run benchmark + regression suite under 3.14; verify parity metrics (latency deltas within ±5%).

**Dependency Rationalization Philosophy**

- Prefer single library per functional concern unless clear differentiated value.
- Defer inclusion of advanced orchestration / vector infra until scale metrics exceed thresholds (e.g., similarity p95 > 500 ms or embedding corpus > 5M rows).
- Remove environment/config duplication (choose one library) and avoid dormant agent frameworks until needed.

**Current Library Audit (Action Codes: KEEP, DEFER, PRUNE)**
| Package / Group | Action | Rationale |
|-----------------|--------|-----------|
| fastapi, uvicorn | KEEP | Required immediately for Next.js frontend data APIs & future agent endpoints. |
| aiohttp | PRUNE | Redundant if httpx suffices for async HTTP calls. |
| httpx | KEEP | Unified sync/async client for future retrieval tasks. |
| altair | KEEP | Declarative quick charts; complements Plotly. |
| plotly | KEEP | Interactive drill & hover; primary interactive layer. |
| matplotlib | DEFER | Only if static fine-grained control needed; can often export Plotly/Altair to static. |
| pydeck | PRUNE | Not using 3D/geo layering yet; re-add when geospatial features scheduled. |
| streamlit, streamlit-aggrid | PRUNE | Replaced by Next.js + React data grid stack. |
| pandas, numpy, pyarrow | KEEP | Core data stack. |
| narwhals | DEFER | Add only when Polars adopted to bridge APIs. |
| polars (not yet) | DEFER | Introduce upon profiling evidence of Pandas bottlenecks. |
| sentence-transformers | KEEP | Embeddings for semantic search & enrichment. |
| langchain-core, langgraph | DEFER | Keep minimal if MCP + lightweight custom retrieval cover needs; integrate only for complex graph agent flows. |
| pydantic-ai | PRUNE (evaluate) | Overlapping with internal prompt scaffolding + pydantic models; keep only if unique value (tool parsing) confirmed. |
| python-decouple | PRUNE | Duplicate config role; standardize on python-dotenv + config.py. |
| langfuse | DEFER | Telemetry optional; ensure no outbound calls if privacy strict—either sandbox self-host or remove. |
| bitsandbytes, peft | DEFER | Add at fine-tuning execution start (adapter training milestone). |
| mcp | KEEP | Core to agent/tool orchestration vision. |
| anyio, sniffio, h11 | KEEP (transitive) | Required by frameworks (FastAPI/httpx/uvicorn) — may reduce when FastAPI deferred (reevaluate). |
| jsonschema stack | KEEP (minimal) | Pydantic covers most validation; may prune explicit jsonschema usage if unused. |
| watchdog | KEEP | Dev auto-reload & file monitoring useful for iteration. |
| tenacity | KEEP | Retry semantics for transient DB / embedding generation steps. |
| psycopg2-binary, asyncpg | KEEP | Keep psycopg2 for sync ETL + asyncpg potential future async tasks (could DEFER asyncpg if no async pipeline yet). |

**Proposed Trim (Immediate Candidates)**

- Remove: aiohttp, python-decouple, pydeck (if not referenced), pydantic-ai (pending review), streamlit, streamlit-aggrid to lighten Python footprint.
- Mark optional in `requirements-optional.txt` for future: matplotlib, langchain-core, langgraph, langfuse, bitsandbytes, peft, narwhals, asyncpg.

**Action Items**

1. Create `requirements-optional.txt` enumerating deferred libs (tracked but not installed by default).
2. Run code search to confirm absence of imports before pruning.
3. Update PRD acceptance criteria (future) to include dependency slimness metric (# direct production deps ≤ target).
4. Add modernization user stories (see Section 10.29) to codify removal & upgrade workflow.
5. Establish periodic (monthly) dependency audit log artifact.

**Success Metrics (Modernization)**

- Cold environment install time reduced by ≥15% after pruning.
- Production dependency count (direct) ≤ 35 in MVP baseline.
- 0 runtime import errors post-prune (validated by automated smoke test).
- 3.14 migration dry run passes all tests & benchmark thresholds.

**Risks & Mitigations**

- Hidden transitive reliance (e.g., code expecting aiohttp session): mitigate with full-text import scan + runtime smoke.
- Over-pruning leading to re-add churn: stage removal via optional file for one cycle before full deletion.
- Divergent environments (dev vs prod): generate and commit a hash manifest after install.

**Upgrade Guardrails**

- No simultaneous major Python upgrade and bulk dependency upgrade—sequence them.
- Keep adapter training pinned to validated CUDA + driver version; record in model card.

**Next Step Recommendation**

- Execute dependency audit script (to be written) producing classification (KEEP/DEFER/PRUNE) JSON to automate future enforcement.

### 8.8 Frontend architecture (Next.js baseline)

The frontend begins on a modern React/Next.js foundation (no interim Streamlit layer) to avoid rewrite risk and enable richer interactivity from day one.

#### 8.8.1 Feature module structure

- `/dashboard` – strategic metrics & tabs (market, agency, competitive, vehicles, projections).
- `/explorer` – advanced opportunity explorer with faceted + semantic search UI.
- `/capabilities` – capability stance editor, gap matrix visualization, manual overrides.
- `/uplift` – win probability & action uplift simulator (interactive weights + scenarios).
- `/ai` – AI data agent console & session history.
- Shared component library under `src/components` (cards, charts, grids, provenance badges, layout shells).
- Utility packages: `src/lib/api` (fetch & schema validation), `src/lib/state` (store/zustand if needed), `src/lib/hooks` (query hooks), `src/styles` (design tokens & theme).

#### 8.8.2 Data access & contract

- FastAPI provides REST endpoints under `/api/v1/*` (metrics, profiles, uplift calculation, semantic search).
- OpenAPI spec auto-generated; `openapi-typescript` (or `openapi-client-axios`) generates TS types.
- Zod runtime validation guards decode responses → narrows types for components.
- Batch endpoints for composite dashboard payloads reduce waterfall requests.

#### 8.8.3 State management

- TanStack Query handles server cache, background refetch, stale time tuning per resource (metrics vs profiles vs embeddings status).
- Local UI ephemeral state (filters, tab, weight sliders) via component state / lightweight Zustand store (only if cross-page synchronization needed).
- URL query params reflect primary filters for deep-linking & shareable states.

#### 8.8.4 Components & theming

- Component library decision (MUI vs Chakra) captured after spike (story GH-115) – both support design tokens & accessible primitives.
- Data grid: AG Grid (enterprise-like features) or MUI Data Grid (lighter) – decision gated on needed virtualization & cell customization complexity.
- Charting: ECharts (performance & theming) primary; Plotly reserved for ad-hoc 3D or complex hover; Altair used internally to prototype Vega-Lite specs then exported to JSON for custom React wrapper if needed.
- Design tokens file (colors, spacing, typography) → passed to both MUI/Chakra theme & ECharts palette to maintain visual consistency.

#### 8.8.5 Performance & optimization

- Code splitting by route & critical component-level dynamic imports (e.g., heavy grid & chart libs) with suspense fallbacks.
- Server-Side Rendering (SSR) for SEO not critical (local app) – prefer Static Site Generation (SSG) / Incremental Static Regeneration (ISR) for rarely changing glossary/help pages, client-side rendering (CSR) for dynamic analytics.
- Avoid large JSON overfetch: metric consolidation endpoint returns compact numeric arrays + label metadata.
- Memoized selectors & virtualization for large tables.

#### 8.8.6 Testing & quality

- Unit: Jest + @testing-library/react for components.
- Integration: Playwright E2E flows (dashboard load, explorer search, uplift scenario edit).
- Accessibility: axe-core automated scan CI gate (0 critical violations).
- Visual regression (optional later): Storybook + Chromatic or local screenshot diff harness.

#### 8.8.7 Security & privacy

- All requests confined to localhost; no analytics scripts or third-party CDNs (package bundling local).
- CSP & security headers applied by FastAPI reverse proxy (helmet-equivalent middleware pattern).
- Strict TypeScript (`strict: true`) + ESLint + Prettier ensure consistent, safe code patterns.

#### 8.8.8 Build & tooling

- Package scripts: `dev` (next dev), `build`, `lint`, `type-check`, `test`, `e2e` (Playwright), `analyze` (bundle size).
- Git hooks (future) via Husky + lint-staged for fast feedback.
- Bundle analysis target: keep initial dashboard JS < 300KB gzip (excluding chart libs loaded lazily).

#### 8.8.9 Open questions & actions

- Data grid selection (AG Grid vs MUI Data Grid) – evaluate complexity vs bundle size.
- Component library (MUI vs Chakra) – accessibility & theming comparison (GH-115).
- Need for offline caching / PWA – decide after baseline usage patterns.
- Potential addition of React Server Components for static data slices (glossary) – evaluate value vs complexity.

#### 8.8.10 Success metrics (frontend foundation)

- Cold load (first meaningful paint of dashboard shell) ≤ 2s.
- Interactive updates (filter change re-render) < 150ms p95 local.
- Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1.
- Zero critical a11y violations in automated scans.
- < 5% cache miss rate on repeat dashboard loads within a session (stale times tuned).

## 9. Milestones & sequencing

### 9.1 Project estimate

- Size: Medium-Large (MVP ~8–10 weeks part-time solo cadence)

### 9.2 Team size & composition

- Team size: 1 (Capture manager / developer / product)

### 9.3 Suggested phases

- **Phase 1**: Baseline data & performance hardening (2 weeks)
  - Validate materialized views, refresh scripts, index review, logging.
- **Phase 2**: Strategic Dashboard completion (core tabs & metrics) (2 weeks)
  - Market, Agency, Competitive, Vehicle, Future Opportunities.
- **Phase 3**: Advanced Opportunity Explorer + Capability Stance (2 weeks)
  - Faceted + semantic search, capability taxonomy editing.
- **Phase 4**: AI Data Agent & export pipeline (2 weeks)
  - Prompt scaffolds, provenance tagging, Markdown export.
- **Phase 5**: Projection + refinement + QA polish (1–2 weeks)
  - Five-year projections, empty state UX, performance tuning.

## 10. User stories

### 10.1 Market overview metrics

- **ID**: GH-001
- **Description**: As a capture manager, I want to view aggregate obligations, award actions, average award value, and active contracts so I can assess market scale quickly.
- **Acceptance criteria**:

  - Metrics load under 5s with default filters.
  - Values sourced from materialized view when filters align; fallback to direct SQL otherwise.
  - Empty state messaging when no rows.

- **ID**: GH-002
- **Description**: As a capture manager, I want quarterly obligation and base award trends to visualize seasonality.
- **Acceptance criteria**:

  - Fiscal year/quarter calculation matches federal FY (Oct–Sep).
  - Cumulative lines reset each FY.
  - Tooltip shows raw quarterly increment + cumulative total.

- **ID**: GH-003
- **Description**: As a capture manager, I want a capture intensity scatter plot showing agencies by award count vs obligation.
- **Acceptance criteria**:
  - Size encodes avg award value (capped at 95th percentile min size=5).
  - Hover reveals agency, award count, total obligation, avg award value.
  - Clicking agency applies agency filter.

### 10.2 Top entities & competition

- **ID**: GH-004
- **Description**: I want to see top agencies by award count and obligation.
- **Acceptance criteria**:

  - Toggle between count/obligation modes.
  - Limit N adjustable (default 15).
  - Sorting consistent with selected metric.

- **ID**: GH-005
- **Description**: I want to view competitor market share (parent + subsidiary) to identify dominant players.
- **Acceptance criteria**:

  - Market share % = competitor obligation / total filtered obligation.
  - Ranks stable under re-filtering.
  - Export CSV of table rows.

- **ID**: GH-006
- **Description**: I want a treemap of competitor vs sub-agency allocation.
- **Acceptance criteria**:

  - Rectangle size = obligation, color = parent contractor.
  - Minimum threshold filters out negligible (<0.1% share) blocks.

- **ID**: GH-007
- **Description**: I want a competitor-agency relationship heatmap for top N competitors.
- **Acceptance criteria**:
  - Top N by obligation; each competitor limited to top 3 agencies.
  - Color scale normalized (0–max competitor-agency obligation in selection).

### 10.3 Future opportunities & projections

- **ID**: GH-008
- **Description**: I want to list expiring base contracts within 6–24 month windows.
- **Acceptance criteria**:

  - Only base awards (modification_number='0').
  - Windows: 0–6, 6–12, 12–24 months.
  - Sorting by days to expiration ascending then obligation descending.

- **ID**: GH-009
- **Description**: I want a five-year projection of potential recompetes with escalation.
- **Acceptance criteria**:
  - Only future quarters beyond current fiscal quarter included.
  - 2% escalation applied per year; assumption documented tooltip.
  - Suitability % applied to produce potential capture value metric.

### 10.4 Agency intelligence

- **ID**: GH-010
- **Description**: I want agency drill-down (top NAICS, PSC, contractors) to tailor positioning.
- **Acceptance criteria**:

  - Each list limited to top 10 by obligation.
  - Selecting item applies secondary filter (where possible) or spawns explorer pre-filter.

- **ID**: GH-011
- **Description**: I want to compare agencies via obligation ratio metrics.
- **Acceptance criteria**:
  - Shows award_count, obligations, avg award value per agency.
  - Normalized log scales for axes available toggle.

### 10.5 Contract vehicle analysis

- **ID**: GH-012
- **Description**: I want to see distribution of award types and contract pricing strategies.
- **Acceptance criteria**:

  - Base awards only for counts; obligations aggregated inclusive of mods.
  - Pie or bar selectable; legend truncation handling.

- **ID**: GH-013
- **Description**: I want agency–vehicle preference insights.
- **Acceptance criteria**:

  - Table of agency vs top vehicles (obligation share) with threshold >1%.

- **ID**: GH-014
- **Description**: I want contract pricing competition/value breakdown.
- **Acceptance criteria**:
  - Two tables: competition (# competitors) & value (obligation, avg per competitor).
  - Standardized abbreviations (e.g., FIXED PRICE WITH EPA).

### 10.6 Geographic analysis

- **ID**: GH-015
- **Description**: I want state-level obligation totals.
- **Acceptance criteria**:
  - Excludes null state codes.
  - Sorted descending; exportable.

### 10.7 Advanced opportunity explorer

- **ID**: GH-016
- **Description**: I want to apply multi-dimensional filters (date, agency, NAICS, PSC, contractor, set-aside, competition, contract type).
- **Acceptance criteria**:

  - Filters combined with AND logic.
  - Clear all button resets to defaults.

- **ID**: GH-017
- **Description**: I want semantic search across descriptions.
- **Acceptance criteria**:

  - Uses vector similarity if embeddings present; fallback lexical ranking.
  - Top K results ranked with similarity score.

- **ID**: GH-018
- **Description**: I want to save and recall search configurations.
- **Acceptance criteria**:

  - Save assigns a unique name; duplicates prompt overwrite confirm.
  - Saved queries persisted locally.

- **ID**: GH-019
- **Description**: I want pagination for large result sets.
- **Acceptance criteria**:
  - Page size options (25/50/100).
  - Row cap guard (>10k) prompts tightening filters.

### 10.8 Capability stance module

- **ID**: GH-020
- **Description**: I want to define internal capabilities (core, differentiators, emerging).
- **Acceptance criteria**:

  - CRUD operations stored locally (JSON or table) with validation.

- **ID**: GH-021
- **Description**: I want inferred competitor capability tags.
- **Acceptance criteria**:

  - Rule-based inference (frequency thresholds in award descriptions / NAICS concentration) documented.
  - Confidence score displayed.

- **ID**: GH-022
- **Description**: I want a capability gap matrix (customer need vs us vs competitors).
- **Acceptance criteria**:
  - Color-coded cells: green (covered), yellow (partial), red (gap).
  - Exportable as Markdown table segment.

### 10.9 AI data agent

- **ID**: GH-023
- **Description**: I want to ask natural language questions about spend trends.
- **Acceptance criteria**:

  - Supports questions mapping to known analytic intents (trend, top entities, projections).
  - Responds with answer + provenance references.

- **ID**: GH-024
- **Description**: I want AI-generated win themes based on selected opportunity context.
- **Acceptance criteria**:

  - At least 3 themes returned with rationale & supporting data points.
  - Flag generative sections clearly ("AI-Generated").

- **ID**: GH-025
- **Description**: I want follow-up question continuity.
- **Acceptance criteria**:

  - Session context retained until manual reset.
  - Context size capped to prevent memory growth.

- **ID**: GH-026
- **Description**: I want to generate a competitive snapshot.
- **Acceptance criteria**:

  - Output: top 5 competitors, market shares, inferred capability edges, set-aside utilization.

- **ID**: GH-027
- **Description**: I want an explanation of how metrics were computed.
- **Acceptance criteria**:
  - "Explain" command returns formula & source view/table names.

### 10.10 Capture profile export

- **ID**: GH-028
- **Description**: I want to export a structured capture profile in Markdown.
- **Acceptance criteria**:

  - Includes mandatory sections (Opportunity Summary, Contract Details, Customer Trends, Our Position, Competitor Landscape, Capability Gaps & Strategy, Win Themes, Recommended Actions).
  - Timestamps and filter snapshot embedded in metadata header.

- **ID**: GH-029
- **Description**: I want AI-drafted narrative blocks inserted into export.
- **Acceptance criteria**:
  - AI blocks delimited & attributable (model name + generation time).

### 10.11 Data ingestion & refresh

- **ID**: GH-030
- **Description**: I want monthly USAspending data refresh.
- **Acceptance criteria**:

  - Incremental fetch by last action_date; dedup successful.
  - Logs entries of row deltas.

- **ID**: GH-031
- **Description**: I want daily SAM.gov placeholder ingestion (stubbed initial pipeline).
- **Acceptance criteria**:
  - Scheduled job creates log entry (no external call until implemented) with TODO marker.

### 10.12 Performance & diagnostics

- **ID**: GH-032
- **Description**: I want query diagnostics (rows, load time) surfaced in UI.
- **Acceptance criteria**:

  - Session state updated for each major data fetch.
  - Display collapsible diagnostics panel.

- **ID**: GH-033
- **Description**: I want manual materialized view refresh control.
- **Acceptance criteria**:
  - Button triggers refresh with progress feedback (success/fail message).

### 10.13 Configuration & privacy

- **ID**: GH-034
- **Description**: I want centralized config access.
- **Acceptance criteria**:

  - All runtime config retrieved exclusively via `config.py`.

- **ID**: GH-035
- **Description**: I want assurance of no outbound AI calls.
- **Acceptance criteria**:
  - Network monitoring / code review ensures only local model endpoints referenced.

### 10.14 Semantic / embedding layer

- **ID**: GH-036
- **Description**: I want embeddings for semantic contract description search.
- **Acceptance criteria**:
  - Vector column populated for new ingestion batch.
  - Mismatch fallback (embedding absent) clearly notified.

### 10.15 Error handling & resilience

- **ID**: GH-037
- **Description**: I want graceful handling of Database (DB) errors.
- **Acceptance criteria**:

  - User sees friendly message + optional stack trace expander.

- **ID**: GH-038
- **Description**: I want empty filter results guidance.
- **Acceptance criteria**:
  - Suggests relaxing specific filters based on cardinality knowledge.

### 10.16 Logging & observability

- **ID**: GH-039
- **Description**: I want AI interactions logged with metadata.
- **Acceptance criteria**:

  - Log row includes prompt, response, model name, latency, token counts (if available), tools used.

- **ID**: GH-040
- **Description**: I want capture profile export actions logged.
- **Acceptance criteria**:
  - Log includes filename, sections included, success/failure.

### 10.17 Capability inference & gaps

- **ID**: GH-041
- **Description**: I want rule-based competitor capability inference.
- **Acceptance criteria**:

  - Rules documented; each inferred capability stores rule ID.

- **ID**: GH-042
- **Description**: I want to adjust inferred capabilities manually.
- **Acceptance criteria**:
  - Manual overrides stored and marked as user-sourced vs inferred.

### 10.18 Win theme recommendation engine

- **ID**: GH-043
- **Description**: I want AI-suggested win themes grounded in data.
- **Acceptance criteria**:
  - Each theme references at least one metric or competitor insight.

### 10.19 Saved explorer queries

- **ID**: GH-044
- **Description**: I want to rename or delete saved queries.
- **Acceptance criteria**:
  - Confirmation prompt on delete.

### 10.20 Provenance & explainability

- **ID**: GH-045
- **Description**: I want a provenance overlay for dashboard metrics.
- **Acceptance criteria**:
  - Clicking info icon reveals: source view, transformation summary, last refresh timestamp.

### 10.21 Markdown export integrity

- **ID**: GH-046
- **Description**: I want deterministic section ordering in exports.
- **Acceptance criteria**:
  - Order matches PRD-defined section list.

### 10.22 Local-only assurance

- **ID**: GH-047
- **Description**: I want a privacy status indicator.
- **Acceptance criteria**:
  - Badge indicates "Local Mode"; turns warning if remote endpoints detected.

### 10.23 Capability stance versioning

- **ID**: GH-048
- **Description**: I want to version capability stance snapshots.
- **Acceptance criteria**:
  - Each save increments revision with timestamp & change summary.

### 10.24 AI session management

- **ID**: GH-049
- **Description**: I want to reset AI conversation context.
- **Acceptance criteria**:
  - Button clears session memory & logs event.

### 10.25 Performance guardrails

- **ID**: GH-050
- **Description**: I want automatic query warning if estimated cost high.
- **Acceptance criteria**:
  - Warning shown if row estimate > threshold (e.g. EXPLAIN result > 5M rows) before execution (future optimization – placeholder messaging in MVP acceptable).

### 10.26 Win probability and uplift modeling

- **ID**: GH-051
- **Description**: I want a baseline heuristic win probability score for a filtered opportunity or set of expiring contracts.
- **Acceptance criteria**:

  - Score in range 0.0–1.0 displayed with qualitative band (Low / Moderate / High).
  - Components (capability coverage, competition intensity, relationship strength, gap severity, teaming leverage) and their weighted contributions listed.
  - Weights configurable via configuration file.

- **ID**: GH-052
- **Description**: I want to simulate adding an action (e.g. teaming partner covering capability gap) and see the change in win probability.
- **Acceptance criteria**:

  - User selects one or more actions from predefined list; system recalculates adjusted probability.
  - Uplift (delta) shown numerically and as percentage relative improvement.
  - Negative or negligible (<2 percentage points) uplift flagged.

- **ID**: GH-053
- **Description**: I want a ranked list of recommended actions ordered by predicted uplift.
- **Acceptance criteria**:

  - Each recommendation shows uplift value, confidence level (heuristic High/Medium/Low), and top 3 driving factors.
  - At least one recommendation references closing a capability gap if any red gaps exist.

- **ID**: GH-054
- **Description**: I want pursuit history (decisions and outcomes) captured for future model training.
- **Acceptance criteria**:

  - Data fields stored: pursuit_id, snapshot_date, baseline_probability, actions_selected (array), action_adjusted_probability, decision (bid/no-bid), outcome (win/loss when known), capability_coverage_score, competitor_count, incumbent_flag.
  - Record created or updated on export or explicit save.

- **ID**: GH-055
- **Description**: I want the export to include recommended actions with predicted uplift and rationale.
- **Acceptance criteria**:

  - "Recommended Actions" section lists top 3 actions with baseline probability, adjusted probability, uplift delta, rationale sentence, and driver feature list.
  - Section clearly labels that uplift is model-predicted and may change as data improves.

- **ID**: GH-056
- **Description**: I want transparency into how win probability was computed.
- **Acceptance criteria**:
  - "Explain win probability" control reveals formula, current weight values, and each component’s raw metric.
  - If any required metric missing, explanation lists missing inputs and fallback assumption used.

### 10.27 AI summarization templates

- **ID**: GH-057
- **Title**: Incumbent Profile Summary
- **Description**: Summarize incumbent performance (obligations trend, period of performance coverage, set-aside usage, recompete timing signals).
- **Acceptance criteria**:

  - Outputs: total obligations, CAGR %, average annual modification count, set-aside pattern, final period days remaining.
  - Flags anomalies (e.g., declining obligations >15% YoY).
  - Provides 1–2 strategic notes (e.g., stability vs volatility) with provenance references.

- **ID**: GH-058
- **Title**: Contract Modification Dynamics Summary
- **Description**: Detect high modification count and characterize requirement dynamism and pricing risk especially for Firm-Fixed-Price (FFP) contracts.
- **Acceptance criteria**:

  - Computes modification density = modifications / months since award.
  - Labels dynamic if density exceeds 75th percentile for similar NAICS & contract type.
  - Highlights top 3 modification reasons (if coded) or value variance when reasons absent.
  - Adds pricing risk note if dynamic AND contract_type = Firm-Fixed-Price (FFP).

- **ID**: GH-059
- **Title**: Capability Gap Narrative
- **Description**: Translate capability gap matrix into concise narrative of strengths, gaps, and priority closures.
- **Acceptance criteria**:

  - Lists top 3 differentiator strengths with supporting evidence metric.
  - Lists up to 5 red or yellow gaps grouped by customer criticality.
  - Recommends at least one teaming or internal development action.

- **ID**: GH-060
- **Title**: Agency Buying Behavior Brief
- **Description**: Summarize an agency's recent buying patterns.
- **Acceptance criteria**:

  - Includes top 5 NAICS & PSC shifts (increase/decrease %) last 3 fiscal years.
  - Notes seasonality: peak award quarter vs median.
  - Notes prevalent contract types and set-aside share.

- **ID**: GH-061
- **Title**: Parent/Subaward Network Summary
- **Description**: Summarize prime–sub relationships for target opportunity context.
- **Acceptance criteria**:

  - Lists top 5 subs by aggregated obligation under target prime.
  - Flags capability fill areas (sub covers a gap category).
  - Suggests potential teaming if analogous gaps appear in current pursuit.

- **ID**: GH-062
- **Title**: Contract Vehicle Utilization Summary
- **Description**: Summarize usage of major contract vehicles relevant to the filtered scope.
- **Acceptance criteria**:

  - Top vehicles with obligation share and trend direction (up/down/flat) over last 3 years.
  - Flags vehicles with approaching on-ramp or recompete (if metadata available).
  - Provides recommendation: pursue existing vehicle, partner, or await on-ramp.

- **ID**: GH-063
- **Title**: Pricing & Competition Dynamics Summary
- **Description**: Summarize competitive intensity and pricing environment.
- **Acceptance criteria**:

  - Average number of competitors per competed award and distribution (median, 90th percentile).
  - Competition type breakdown (% full/open vs limited vs sole source).
  - Notes any spike in protests (placeholder if data unavailable).

- **ID**: GH-064
- **Title**: Action Uplift Scenario Recap
- **Description**: Summarize top recommended actions from win probability modeling.
- **Acceptance criteria**:

  - Lists top 3 actions with baseline probability, adjusted probability, uplift delta.
  - Provides rationale phrase referencing capability or competitive driver.
  - Warns if any action relies on low-confidence inference.

- **ID**: GH-065
- **Title**: Data Coverage & Quality Summary
- **Description**: Summarize data sufficiency and gaps affecting analysis confidence.
- **Acceptance criteria**:

  - Shows row counts vs expected baseline (e.g., coverage % of historical period).
  - Lists missing critical fields (e.g., NAICS, PSC) if >5% null.
  - Assigns confidence band (High/Medium/Low) with reasoning.

- **ID**: GH-066
- **Title**: Set-Aside Participation Summary
- **Description**: Summarize set-aside utilization patterns vs company profile.
- **Acceptance criteria**:
  - Percentage obligations by set-aside category and trend direction.
  - Compares internal eligibility categories vs agency usage.
  - Recommends pursuit or teaming strategy for underrepresented categories.

All summaries must:

- Provide provenance references (view/table names) for each quantitative statement.
- Complete generation in <3 seconds on target hardware for default filter scope.
- Degrade gracefully (state "Insufficient data" with reason) when required metrics unavailable.

### 10.28 Data enrichment & knowledge layer

- **ID**: GH-067
- **Description**: As a capture manager, I want canonical entity resolution so company, agency, and contract vehicle references link to stable internal identifiers.
- **Acceptance criteria**:

  - Resolution tables store: source_id, normalized_name, canonical_entity_id, entity_type, created_at, updated_at.
  - Collision (two sources -> same canonical) logged with merge record.
  - Unresolvable entities flagged with status "unmatched" (<2% of total entities after first pass).

- **ID**: GH-068
- **Description**: I want cleaned & normalized textual fields for semantic processing.
- **Acceptance criteria**:

  - Normalization includes: unicode NFC, lowercase, punctuation stripped (except hyphen in NAICS-like tokens), multiple whitespace collapsed.
  - Stored alongside original in interim schema with suffix \_clean.
  - Coverage report lists % of rows cleaned (>99%).

- **ID**: GH-069
- **Description**: I want embeddings generated for new or changed description records without reprocessing the entire corpus.
- **Acceptance criteria**:

  - Incremental job selects rows where embedding_vector IS NULL OR updated_at > last_embedding_timestamp.
  - Batch size configurable; logs processed count & duration.
  - Drift check computes mean cosine distance vs previous 30-day centroid; warning if >0.15.

- **ID**: GH-070
- **Description**: I want attribute inference to fill missing NAICS or Product Service Codes (PSC) using heuristics and similarity.
- **Acceptance criteria**:

  - Inference attempts only when original field NULL.
  - Confidence score >=0.6 required; else left NULL with note.
  - Rule/model id stored; per-run success rate logged.

- **ID**: GH-071
- **Description**: I want capability tag extraction from award descriptions to augment company profiles.
- **Acceptance criteria**:

  - Tags limited to controlled vocabulary (capability taxonomy) + emerging tokens (top TF-IDF terms passing whitelist).
  - Each tag record contains source_award_id, tag, confidence, extraction_method (rule|model), provenance reference.
  - False positive rejection workflow (manual remove) updates suppression list.

- **ID**: GH-072
- **Description**: I want a requirement profile view aggregating historical indicators for a single requirement/opportunity.
- **Acceptance criteria**:

  - Includes: obligation trend (3Y), modification density, average competitors, incumbent contractor, pricing type distribution.
  - Refreshes incrementally when constituent raw rows change.
  - View name and last refresh timestamp accessible to AI agent for provenance.

- **ID**: GH-073
- **Description**: I want a company profile view summarizing multi-year posture.
- **Acceptance criteria**:

  - Includes: 5-year obligations, CAGR, top 5 agencies concentration %, capability tag distribution, set-aside utilization breakdown, teaming partner count.
  - Computed via materialized view (refresh manual MVP) under s3_processed.
  - Null-sensitive metrics (e.g., CAGR with single year) degrade with explanatory placeholder.

- **ID**: GH-074
- **Description**: I want enrichment provenance and confidence visible for inferred fields.
- **Acceptance criteria**:

  - Inferred columns accompanied by _\_confidence and _\_source fields.
  - UI hover displays rule/model id and timestamp.
  - Missing provenance flagged in diagnostics (<0.5% rows allowed).

- **ID**: GH-075
- **Description**: I want change detection to target only modified entities for re-embedding and re-inference.
- **Acceptance criteria**:

  - Change table tracks primary_key, change_type (insert|update), detected_at.
  - Enrichment job processes only listed keys then clears them (transactionally) upon success.
  - Metrics: average lag from change detection to enrichment < 10 minutes (manual trigger MVP — measure only).

- **ID**: GH-076
- **Description**: I want a knowledge graph edge table capturing relationships (company–agency, company–vehicle, company–NAICS, opportunity–company incumbent) with weights.
- **Acceptance criteria**:

  - Edge table schema: src_type, src_id, dst_type, dst_id, edge_type, weight, first_seen, last_seen.
  - Weight definition documented (e.g., normalized obligation share or frequency).
  - Snapshot exportable to support future graph algorithms.

- **ID**: GH-077
- **Description**: I want cached semantic fingerprints (cluster centroids) for grouping similar opportunities.
- **Acceptance criteria**:

  - Clustering job runs on embeddings (only base awards) producing cluster_id, centroid_vector, size, top_terms.
  - Minimum cluster size threshold configurable (default 5); singletons labeled outlier.
  - Stored metadata accessible for future opportunity clustering feature.

- **ID**: GH-078
- **Description**: I want enrichment quality scoring to monitor inference precision risk.
- **Acceptance criteria**:

  - Quality score computed per batch: inferred_fields_filled / inference_attempts.
  - Alert flag if score < target threshold (e.g., 0.7) or coverage drops >10% vs prior batch.
  - Logged with batch identifier.

- **ID**: GH-079
- **Description**: I want MCP (Model Context Protocol) orchestration tasks defined for each enrichment stage for future automation.
- **Acceptance criteria**:

  - Task registry (JSON/YAML) lists task_id, description, trigger (manual|schedule|dependency), inputs, outputs.
  - At least: entity_resolution, text_normalization, embedding_generation, attribute_inference, profile_refresh, change_detection_scan, clustering, quality_audit.
  - AI agent can retrieve task list and status for reasoning (read-only MVP).

- **ID**: GH-080
- **Description**: I want the AI data agent to leverage enriched profiles and provenance when answering questions.
- **Acceptance criteria**:

  - Agent retrieval layer queries profile views first before raw award tables when context matches (company or requirement analysis intent).
  - Responses cite profile view names and enrichment confidence where applicable.
  - Fallback path logged if profile view stale or missing.

- **ID**: GH-081
- **Description**: I want a similarity lookup utility to quickly find related historical requirements to a target opportunity.
- **Acceptance criteria**:

  - Uses embedding ANN (Approximate Nearest Neighbor) or brute-force if corpus < threshold.
  - Returns top 10 with similarity scores and cluster_id where available.
  - Average lookup latency < 500 milliseconds for corpus size in MVP scale.

- **ID**: GH-082
- **Description**: I want a data completeness dashboard for enrichment-critical fields.
- **Acceptance criteria**:

  - Displays NULL rates over time for key fields (NAICS, PSC, competition type, contract vehicle, incumbent flag).
  - Highlights changes >5 percentage points week-over-week.
  - Exports completeness snapshot to logs.

- **ID**: GH-083
- **Description**: I want requirement profile generation latency to stay within performance bounds.
- **Acceptance criteria**:

  - Profile view refresh (single target) under 2 seconds median.
  - Bulk refresh (top 100 changed requirements) under 60 seconds.
  - Latency metrics logged.

- **ID**: GH-084
- **Description**: I want company profile refresh latency tracked.
- **Acceptance criteria**:

  - Single company profile recompute < 3 seconds median.
  - Stale profile (older than 30 days) flagged in UI.
  - Metrics recorded in enrichment job log table.

- **ID**: GH-085
- **Description**: I want semantic embedding drift monitoring and alerting.
- **Acceptance criteria**:

  - Drift metric = average cosine distance between current batch centroid and rolling 30-day centroid.
  - Alert threshold configurable; alert row written when exceeded.
  - Drift panel available in diagnostics.

- **ID**: GH-086
- **Description**: I want a consistent provenance taxonomy for enrichment steps.
- **Acceptance criteria**:

  - Standard codes (ER, CLEAN, EMBED, INFER, PROFILE, CLUSTER, DRIFT, QUALITY) documented.
  - Each enrichment log entry uses one of these codes.
  - Undefined code usage rate = 0.

- **ID**: GH-087
- **Description**: I want manual override workflow for incorrect inferred attributes.
- **Acceptance criteria**:

  - Override table stores entity_id, attribute, old_value, new_value, reason, user_tag, timestamp.
  - Overrides applied after inference in view logic.
  - Reconciliation report lists overrides >30 days old for review.

- **ID**: GH-088
- **Description**: I want enrichment re-run simulation (dry-run) to show prospective changes before committing.
- **Acceptance criteria**:

  - Dry-run flag logs projected counts (adds/updates) without writing.
  - Diff summary includes entity counts by attribute type.
  - Commit only proceeds when not dry-run.

- **ID**: GH-089
- **Description**: I want enrichment batch versioning for reproducibility.
- **Acceptance criteria**:

  - Batch table includes batch_id (timestamp + hash), stages executed, row counts, success flag, duration.
  - Profiles reference last successful batch_id.
  - Ability to list last 10 batches with stats.

- **ID**: GH-090
- **Description**: I want the AI summarization templates to automatically incorporate enriched profile fields when available.
- **Acceptance criteria**:
  - Templates check presence of profile view columns; if missing, degrade with placeholder note.
  - At least 3 templates (Incumbent, Capability Gap, Agency Buying Behavior) validated against enriched profile fields.
  - Provenance lines include enrichment stage code.

### 10.29 Modernization & dependency consolidation

- **ID**: GH-106
- **Description**: As a developer, I want a dependency audit report classifying each library as KEEP/DEFER/PRUNE.
- **Acceptance criteria**:

  - Script outputs JSON with fields: package, version, classification, rationale.
  - Report stored under `reports/dependency_audit.json`.
  - Zero UNKNOWN classifications.

- **ID**: GH-107
- **Description**: I want unneeded libraries pruned into an optional requirements file.
- **Acceptance criteria**:

  - `requirements.txt` contains only KEEP libraries.
  - `requirements-optional.txt` lists DEFER libraries with inline comments.
  - Import scan confirms no active code references for PRUNEd packages.

- **ID**: GH-108
- **Description**: I want automated verification that pruning did not introduce import errors.
- **Acceptance criteria**:

  - Smoke test script imports all top-level modules; exits 0.
  - CI (future) gate fails if any ImportError encountered.

- **ID**: GH-109
- **Description**: I want a Python 3.14 readiness checklist executed prior to migration.
- **Acceptance criteria**:

  - Checklist markdown includes: deprecated warnings scan, benchmark comparison, dependency wheels availability.
  - All items marked PASS before upgrade commit.

- **ID**: GH-110
- **Description**: I want a dependency slimness metric tracked over time.
- **Acceptance criteria**:
  - Metric (# direct deps) logged after each audit; sparkline or history stored in JSON.
  - Alert (log warning) if count increases by >10% without associated user story reference.

### 10.30 Frontend foundation (Next.js)

- **ID**: GH-111
- **Description**: As a developer, I want a Next.js dashboard shell with navigation, layout, and design tokens to serve as the baseline for feature modules.
- **Acceptance criteria**:

  - Layout includes persistent sidebar (filters placeholder) and top bar (title + status badges).
  - Global theme tokens (color, spacing, typography) defined and applied to at least 3 primitive components.
  - Lighthouse performance & accessibility categories ≥ 90 local.

- **ID**: GH-112
- **Description**: I want FastAPI endpoints delivering consolidated metric payloads consumed by the dashboard shell.
- **Acceptance criteria**:

  - Endpoint: /api/v1/metrics/market returns aggregated metrics & time series in compact JSON (numeric arrays + label map).
  - OpenAPI spec generates TypeScript types; build fails if mismatch (type generation step).
  - p95 endpoint latency < 300ms with warm DB cache.

- **ID**: GH-113
- **Description**: I want an interactive Action Uplift Simulator page with real-time probability recalculation.
- **Acceptance criteria**:

  - Weight slider changes trigger recalculation <150ms (debounced) client-side.
  - Scenario list diffing preserves focus & minimal re-renders (React profiler commit duration < 30ms typical update).
  - Jest tests cover baseline probability recompute logic (≥ 2 scenarios test cases).

- **ID**: GH-114
- **Description**: I want a schema validation layer ensuring API responses conform (prevent silent contract drift).
- **Acceptance criteria**:

  - Zod (or generated validators) parse responses; invalid shape logs structured error & surfaces toast.
  - Test injects malformed payload -> validation failure path observed with clear message.
  - Zero uncaught type assertion errors during smoke run.

- **ID**: GH-115
- **Description**: I want a documented component library decision (MUI vs Chakra) with evaluation outcomes.
- **Acceptance criteria**:
  - Comparison doc lists: bundle size, theming flexibility, accessibility primitives, data grid ecosystem fit.
  - Decision captured in decision log (new entry D-011) with revisit trigger.

## 11. Additional enhancement ideas (post-MVP candidates)

- Opportunity clustering (semantic grouping of similar expiring contracts).
- Risk scoring (data completeness, competition intensity, deobligation volatility).
- Subcontract network inference (graph of prime–subaward relationships for teaming angle analysis).
- Win theme effectiveness feedback loop (track which exported themes correlate with pursuit success).
- Automated agency brief generation (multi-page narrative from parameterized template).
- Capability maturity radar visualization.
- True causal uplift modeling (transition from heuristic to two-model or meta-learner approach once sufficient labeled pursuits accumulated).
- Scenario planning dashboard (batch compare multiple action combinations and produce efficient frontier of effort vs uplift).
- Confidence calibration using reliability curves after >100 labeled outcomes.

## 12. Assumptions & open questions

- SAM.gov integration details (API method, data fields) pending; placeholder architecture stands.
- Embedding generation approach (model choice, batch size) to be finalized after initial performance tests.
- Win theme evaluation criteria (qualitative acceptance) to be formalized later.

## 13. Risks & mitigations

- Schema drift: Mitigate via automated schema diff logging + alert.
- Embedding storage bloat: Periodic pruning of low-value text fields; consider dimensionality reduction later.
- AI hallucination: Enforce retrieval-grounded answer templates + provenance display.
- Performance regression: Baseline query benchmarks stored; add simple regression script.

## 14. Glossary (selected)

- Base Award Action: First (modification_number='0') transaction establishing the contract.
- Obligation: Federal action obligation dollar amount (positive/negative adjustments included in net metrics).
- Suitability Percentage: User-defined potential capture share applied to projection value.
- Capability Stance: Canonical internal capability profile used for comparative analysis.
- Win Theme: Persuasive strategic narrative aligning capabilities to customer needs and differentiators.
- Win Probability: Estimated likelihood of winning a specific opportunity under current state assumptions.
- Uplift (Win Probability Uplift): Incremental change in win probability attributable to a proposed action or combination of actions compared to the baseline scenario.
- Action Recommendation: A suggested discrete step (e.g., add teaming partner with cyber capability) that increases predicted win probability by a positive uplift amount.
- Modification: A contractual change (administrative or substantive) recorded against a base award.
- Modification Density: Count of modifications divided by months since base award effective date.
- Dynamic Requirement: A contract exhibiting high modification density relative to peer benchmarks, implying evolving scope or uncertainty.
- Firm-Fixed-Price (FFP): Contract type with fixed total price creating higher risk when requirements are dynamic.
- Entity Resolution: Process of mapping multiple raw source identifiers or name variants to a single canonical entity record.
- Canonical Entity Identifier (CEID): Internal stable unique identifier assigned during entity resolution to represent a consolidated entity.
- Enrichment Layer: Set of processes and artifacts (normalized text, inferred attributes, embeddings, profiles) augmenting raw data for advanced analytics and AI.
- Knowledge Layer: Structured representation (profiles, knowledge graph edges, semantic fingerprints) enabling contextual retrieval and reasoning.
- Requirement Profile: Aggregated feature set describing a single requirement or opportunity (trends, dynamics, competition, pricing, incumbent data).
- Company Profile: Aggregated feature set summarizing an organization's historical performance and positioning (spend, concentration, capabilities, teaming network).
- Provenance (Enrichment): Metadata linking an inferred or transformed value to its source rule, model, or original record.
- Embedding Drift: Change over time in the distribution of embedding vectors indicating potential semantic shift or model inconsistency.
- Change Detection Window: Time-bounded scope within which modifications are scanned for targeted reprocessing.
- Attribute Confidence Score: Numeric (0–1) indicator of certainty for an inferred attribute value.
- Semantic Fingerprint: Cluster centroid or reduced representation capturing the semantic essence of a group of related text records.
- Similarity Cluster: Group of requirements or opportunities grouped by vector similarity above a threshold.
- Knowledge Graph Edge: A stored relationship between two entities (e.g., company–agency) with a weight representing strength or volume.
- Batch Identifier (Batch ID): Unique token (timestamp + hash) representing one full execution of the enrichment pipeline stages.
- Dry-Run (Enrichment): Execution mode that simulates changes without persisting modifications, providing counts and diffs only.
- Instruction Tuning: Process of fine‑tuning a base Large Language Model (LLM) on curated instruction–response pairs to improve task following.
- LoRA (Low-Rank Adaptation): Parameter-efficient fine‑tuning technique injecting trainable low‑rank matrices without modifying original model weights.
- PEFT (Parameter-Efficient Fine-Tuning): Family of approaches (LoRA, Prefix Tuning, adapters) enabling adaptation with small trainable parameter sets.
- RAG (Retrieval-Augmented Generation): Pattern where external knowledge (e.g., vector or profile store) is retrieved and injected into the model prompt for grounded answers.
- Synthetic Data (LLM): Model-generated instruction–response examples used to expand coverage of query intents while controlling style and structure.
- Knowledge Distillation (LLM): Technique of using outputs from a larger or more capable model (teacher) to train a smaller target model (student), under licensing and privacy constraints.
- Style Token: Special control token indicating desired narrative tone or template (e.g., CAP_PROFILE, GAP_SUMMARY) in instruction tuning.
- Grounding Score: Evaluation metric quantifying fraction of assertions in an answer that directly map to retrieved or cited source data.
- Citation Accuracy: Percentage of citations that actually support the referenced claim.
- Hallucination Rate: Percentage of answers containing unsupported or fabricated facts relative to evaluation set size.
- Data Dictionary (LLM Context): Structured specification of fields, types, business meaning, and usage notes used to generate consistent prompts and training examples.

## 15. Acceptance & release criteria

- All High priority features’ user stories (IDs GH-001..GH-009, GH-010, GH-016..GH-024, GH-028, GH-032, GH-034, GH-035, GH-039, GH-043, GH-067..GH-073, GH-074, GH-075, GH-076, GH-077, GH-078, GH-079, GH-080, GH-081, GH-082, GH-083, GH-084, GH-085, GH-086, GH-087, GH-089, GH-090) implemented and passing acceptance tests. (Some enrichment operational stories may launch in read-only/ manual trigger mode but still meet criteria.)
- Dashboard median load time (default filters) ≤ 5s on target hardware (64 Gigabytes (GB) Random Access Memory (RAM) + RTX 4060).
- Exported capture profile contains all mandated sections & provenance metadata.
- AI agent responses cite at least one provenance reference in ≥90% of analytic queries.

## 16. LLM fine-tuning & adaptation strategy

### 16.1 Objectives

- Improve task adherence for capture-specific analytical and narrative prompts (win themes, incumbent profile, capability gap narrative).
- Reduce hallucination and enforce provenance-aware phrasing.
- Optimize smaller local models (7B–13B) for latency while retaining domain fidelity using parameter-efficient fine-tuning (PEFT) (LoRA adapters).
- Establish reproducible, auditable pipeline linking raw data -> curated examples -> training artifacts -> evaluation metrics -> deployment.

### 16.2 Data sources for tuning

- `docs/CAPTUREINTEL.md` (data dictionary & schema semantics) – becomes canonical field description source.
- Historical contract & award records (cleaned + enriched profiles) – structured factual grounding.
- Existing dashboard queries & visualization configs – source for generating instruction patterns ("Provide a bar chart narrative for top 5 agencies by obligation last FY").
- Synthetic user inquiry generation (seeded by larger offline model, manually audited) to expand long-tail intents (e.g., scenario simulations, uplift what-if questions).
- Reformatted Shipley Associates business development guide excerpts (converted to structured sections: phase, artifact type, key decision factors) – caution: only non-proprietary and license-compliant excerpts; internal transformation produces derived guidance dataset.
- Style exemplars: curated high-quality human-authored narratives (redacted proprietary content) establishing tone & structure tokens.

### 16.3 Data curation pipeline (stages)

1. Source ingestion: Collect raw text/structured sources; hash and register in data catalog.
2. Extraction & segmentation: Split documents into semantically coherent chunks (token length targets: 512–1024) preserving citation metadata.
3. Instruction synthesis: Generate instruction–response pairs using templates + synthetic augmentation; enforce JSON schema for metadata.
4. Deduplication & overlap control: MinHash / embedding similarity filtering (threshold cosine >0.92 removed) to avoid near-duplicate leakage.
5. Safety & compliance filtering: Remove PII, proprietary, or license-restricted segments (regex + heuristic + manual spot checks).
6. Formatting & tokenization preview: Validate token length distribution and truncation rate (<3% examples truncated).
7. Train/val/test stratification: Stratify by intent category (analysis, narrative, explanation, projection, what-if) maintaining distributional balance.
8. Quality assurance: Spot evaluate 1% random sample; flag issues (unsupported claim, formatting drift).
9. Packaging: Output consolidated JSONL shards (size ~2–50MB) with reproducible manifest (hash + counts).
10. Versioning: Tag dataset release (e.g., ds_capture_v0.1) referencing source commit hashes & enrichment batch IDs.

### 16.4 Model adaptation approach

- Base local models: llama3-8B, mistral-7B, phi-3 mini (subject to quality vs latency tests).
- Parameter-efficient fine-tuning: LoRA rank 16–32, alpha 32, dropout 0.05; QLoRA (4-bit NF4) for constrained VRAM scenarios.
- Mixed precision (bfloat16/fp16) on RTX 4060; gradient accumulation to simulate effective batch size 128 (micro-batch 4–8).
- Training scheduler: cosine decay with warmup 5% steps.
- Learning rate (LR) search: small sweep (5e-5, 3e-5, 1e-5) evaluating validation grounding score & hallucination rate.
- Early stopping if no improvement in composite score (weighted: 0.5 grounding + 0.3 instruction adherence + 0.2 style conformity) across 3 eval checkpoints.
- Separate adapters per intent cluster (analysis vs narrative) OR unified multi-task adapter with style tokens; decision based on ablation.

### 16.5 Retrieval-augmented generation (RAG) interplay

- Prefer lightweight adapter + strong retrieval context over overfitting model memorization.
- Prompt template integrates: system role (policy), structured context blocks (profiles, metric tables), user question, style token, citing instructions.
- Evaluation distinguishes errors due to retrieval (coverage miss) vs generation (unsupported claim despite evidence present).

### 16.6 Evaluation metrics

- Grounding score: (# supported assertions) / (total assertions) – target ≥0.9.
- Hallucination rate: unsupported assertions per 100 answers – target ≤5.
- Citation accuracy: cited sources truly contain referenced fact – target ≥0.95.
- Instruction adherence: template fields correctly populated – target ≥0.95.
- Compression efficiency: average token reduction vs baseline verbose output – target ≥10% without information loss (manual audit sample).
- Latency: p95 generation time for 512 token output ≤ 2.5s (GPU).

### 16.7 Governance & reproducibility

- Dataset manifest + model card stored in `models/` directory with config parameters, dataset hashes, evaluation table.
- Training run metadata (hyperparameters, git commit, environment) captured in JSON log (e.g., `training_runs/run_<timestamp>.json`).
- Audit script verifies dataset hash consistency before deploying new adapter.
- Rollback procedure: maintain last known good adapter symlink; atomic swap on validation pass.

### 16.8 Deployment & integration

- Serve adapters via Ollama custom model definitions referencing base model + LoRA weights (local only).
- Versioned adapter selection in config (`LLM_ADAPTER_VERSION`).
- Automatic warm-up: run small prompt set at startup to populate caches & measure baseline latency.
- Fallback chain: preferred tuned model -> base model + richer retrieval -> minimal model (for resilience).

### 16.9 Risks & mitigations (LLM-specific)

- Overfitting to synthetic style: maintain ≥30% organic (non-synthetic) examples in train set.
- Data leakage of proprietary guidance: sanitize Shipley-derived text; keep only abstracted patterns.
- Drift from schema changes: regenerate instruction examples referencing new fields; maintain schema version tag in each example.
- Evaluation blindness: periodic manual blind review of generated narratives vs ground truth tables.

### 16.10 User stories (LLM adaptation)

- **ID**: GH-091
- **Description**: As a developer, I want a curated instruction–response dataset manifest for transparency and reproducibility.
- **Acceptance criteria**:

  - Manifest JSON lists dataset shards with hash, size, example count, intent distribution.
  - Stored under `datasets/manifest.json` with schema version.

- **ID**: GH-092
- **Description**: I want automated example generation from existing dashboard queries.
- **Acceptance criteria**:

  - Script enumerates saved query definitions, outputs instruction templates referencing metrics.
  - At least 200 unique analysis examples generated in MVP.

- **ID**: GH-093
- **Description**: I want Shipley guide content converted into structured strategy pattern examples without proprietary wording.
- **Acceptance criteria**:

  - Sanitization script outputs JSONL with fields: phase, artifact_type, strategic_factor, abstracted_guidance.
  - Manual review sample (20 items) shows zero proprietary phrases.

- **ID**: GH-094
- **Description**: I want synthetic user inquiries augmented where gaps exist in intent coverage.
- **Acceptance criteria**:

  - Coverage report shows % of intents; any below 5% boosted to ≥8% after synthesis.
  - Synthetic examples flagged synthetic=true.

- **ID**: GH-095
- **Description**: I want a parameter-efficient fine-tuning configuration stored with defaults.
- **Acceptance criteria**:

  - Config file includes model_name, lora_r, lora_alpha, dropout, target_modules, learning_rate, batch params.
  - Validation ensuring mandatory fields present.

- **ID**: GH-096
- **Description**: I want a training script that outputs evaluation metrics at each checkpoint.
- **Acceptance criteria**:

  - Metrics JSON appended per checkpoint: grounding, hallucination_rate, citation_accuracy, instruction_adherence, loss.
  - Early stop triggers when composite stagnates per spec.

- **ID**: GH-097
- **Description**: I want an evaluation harness that computes grounding and citation accuracy automatically.
- **Acceptance criteria**:

  - Harness loads eval set, performs retrieval, generates answers, parses assertions vs sources.
  - Outputs summary report stored under `eval/reports/`.

- **ID**: GH-098
- **Description**: I want style tokens controlling narrative tone in prompts.
- **Acceptance criteria**:

  - Tokens recognized: CAP_PROFILE, GAP_SUMMARY, AGENCY_BRIEF, ACTION_UPLIFT.
  - At least 90% of generated outputs incorporate style-specific structural elements.

- **ID**: GH-099
- **Description**: I want a rollback mechanism for adapters.
- **Acceptance criteria**:

  - Symlink `current_adapter` updated only after success metrics meet thresholds.
  - Previous symlink retained as `prev_adapter` for instant fallback.

- **ID**: GH-100
- **Description**: I want retrieval-aware prompts automatically cite source view names.
- **Acceptance criteria**:

  - Template enforces presence of at least one citation placeholder; missing placeholder aborts generation.
  - 95% of eval outputs contain ≥1 correct citation.

- **ID**: GH-101
- **Description**: I want hallucination detection sampling to run post-deployment.
- **Acceptance criteria**:

  - Daily sample of 25 queries executed; hallucination rate logged; alert if > target.
  - Log retained 30 days.

- **ID**: GH-102
- **Description**: I want adapter performance benchmarks recorded.
- **Acceptance criteria**:

  - Latency + token throughput recorded for baseline vs tuned model.
  - Report stored with timestamp & hardware spec.

- **ID**: GH-103
- **Description**: I want dataset version tags embedded in generated answers for traceability (internal metadata, not user-visible).
- **Acceptance criteria**:

  - Internal metadata JSON includes dataset_version, adapter_version.
  - Logged with each AI interaction.

- **ID**: GH-104
- **Description**: I want automatic exclusion of leakage-prone examples (answers repeating large verbatim source text segments > N tokens).
- **Acceptance criteria**:

  - Pre-training filter removes examples with >40% verbatim overlap; counts logged.
  - Leakage filter false positive rate <5% (manual sample of 50 removed examples).

- **ID**: GH-105
- **Description**: I want a model card documenting capabilities, limitations, and evaluation metrics.
- **Acceptance criteria**:
  - Model card markdown includes: intended use, not intended use, training data summary, metrics table, ethical considerations, version history.
  - Stored under `models/model_card_<version>.md`.

### 16.11 Out-of-scope (initial adaptation)

- Full RLHF (Reinforcement Learning from Human Feedback) loop (deferred until sufficient human feedback volume collected).
- Advanced guardrail classifier fine-tuning (initial rely on heuristic + structured prompt constraints).
- Multi-lingual adaptation (English only MVP).

### 16.12 KPIs (LLM adaptation)

- Composite evaluation score ≥ baseline +15%.
- Hallucination rate ≤ 5%.
- Median latency change vs base ≤ +10% (or improved).
- ≥90% adoption of tuned adapter (vs manual override to base) after one week.

## 17. Non-functional requirements (NFRs)

### 17.1 Performance

- Dashboard filtered view (default 6 FY, single NAICS) median load ≤ 5s; p95 ≤ 7s.
- Materialized view refresh (core set) ≤ 90s baseline dataset; incremental enrichment (≤5% change) ≤ 10m.
- AI generation (512 output tokens) p95 ≤ 2.5s (tuned 7B) with retrieval context ≤ 2k tokens.
- Similarity lookup (top 10) p95 ≤ 500ms corpus < 1M rows; reassess architecture beyond 1M embeddings or p95 > 700ms.

### 17.2 Reliability & resilience

- Single-user local deployment (no HA); target crash-free sessions ≥ 99% over 30-day period.
- Graceful degradation paths: (a) GPU unavailable → CPU fallback + length reduction; (b) Embedding index missing → lexical fallback; (c) Stale materialized view (>24h) → warning banner.
- All enrichment steps idempotent (re-runs produce same state absent new raw data) and logged with batch_id.

### 17.3 Maintainability

- Module files ≤ 500 LOC; cyclomatic complexity hotspots (>15) flagged for refactor backlog.
- Test coverage (statements) ≥ 60% MVP (focus: data transforms, enrichment logic, win probability model) with trajectory to 80% post-MVP.
- Lint (black + ruff/flake8 style) clean; type checking (mypy/pyright planned) zero errors on critical paths.

### 17.4 Observability

- Structured JSON logs for: queries, enrichment batches, AI interactions, errors.
- Minimal diagnostics panel surfaces latest: query latency p50/p95, embedding drift metric, enrichment backlog size.
- Optional telemetry libs must be disabled by default (no outbound network).

### 17.5 Security & privacy

- No external network calls for AI; enforced via configuration guard + periodic static import scan.
- Local data only; no PII enrichment; any future external integration must pass privacy review checklist.
- Secrets limited to DB connection params; all sourced through `.env` (never committed) and validated on start.

### 17.6 Data quality

- Critical field null thresholds: NAICS < 5%, PSC < 8%, competition_type < 10%; exceeding triggers quality warning banner.
- Inference precision target: attribute inference success (confidence ≥0.6) ≥ 70% of eligible nulls; drift monitored.
- Provenance coverage: ≥ 99.5% inferred fields have \_source + \_confidence columns populated.

### 17.7 Usability & accessibility (internal scope)

- Consistent keyboard navigation for primary filters and export actions.
- Color palettes maintain ≥ 4.5:1 contrast for core text vs background (WCAG AA); automated a11y test suite enforces.
- Tooltip help text present for every metric card (≥ 95% coverage) linking to glossary term when applicable.

### 17.8 Portability

- Rebuild steps documented; fresh clone → functional dashboard ≤ 10 minutes on baseline hardware.
- No system-wide package installs required (pure venv); optional Docker recipe post-MVP.

### 17.9 Scalability thresholds & re-architecture triggers

- Embedding corpus > 1M rows OR similarity p95 > 700ms → evaluate external ANN (Qdrant/Faiss) spike.
- Profile refresh median > 3s sustained → assess additional materialized sub-views / incremental maintenance.
- Memory utilization > 80% during standard operations → consider Polars adoption / chunking enhancements.

### 17.10 Resource utilization targets

- Peak RAM for default dashboard interaction ≤ 8GB.
- GPU VRAM headroom ≥ 1.5GB during inference batches (abort or shrink batch otherwise).

### 17.11 Compliance & auditability

- Basic Software Bill of Materials (SBOM) generation (post-MVP task) to list direct deps with hashes.
- Dependency audit log retained for ≥ 6 months.
- Model adapter card includes dataset and parameter hashes for traceability.

### 17.12 Internationalization & localization

- Out of scope MVP (English only) – note for future: isolate user-facing strings for potential extraction.

### 17.13 Extensibility

- New enrichment stage must register: task_id, inputs, outputs, provenance code; acceptance: integration test calling stage stub.
- Plugin-style AI templates: each registers schema (inputs, output fields, provenance requirements).

## 18. Constraints & principles

### 18.1 Hard constraints

- Local-only processing (air-gapped acceptable) – disallow outbound HTTP except explicit whitelisted future data sources.
- Single-user interactive session model (no concurrency contention design in MVP).
- Python ecosystem only (no polyglot microservices) for MVP maintainability.
- Privacy: No retention of user prompts beyond local logs; logs remain local.

### 18.2 Architectural principles

- Minimize moving parts first; add services (API layer, schedulers) only when forced by new requirements.
- Favor explicit SQL for analytic heavy-lifts (traceable query plans) vs opaque ORM chains.
- Retrieval > memorization: lean prompts enriched with factual profile slices; avoid expanding base model size prematurely.
- Incremental enrichment (changed rows only) to conserve compute.

### 18.3 Technical debt boundaries

- Accept temporary duplication for clarity only if refactor scheduled (<2 sprints) and tracked in backlog.
- Disallow silent exception swallowing in enrichment pipeline (must log and surface summary count of failures).

## 19. Decision log (abbreviated)

| ID    | Date       | Decision                         | Alternatives Considered        | Rationale                                                       | Revisit Trigger                                       |
| ----- | ---------- | -------------------------------- | ------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------- |
| D-001 | 2025-08-15 | Streamlit for UI (superseded)    | Custom React, Dash             | Fast iteration, single dev velocity (initial)                   | Replaced by D-011 (Next.js baseline)                  |
| D-002 | 2025-08-15 | PostgreSQL + pgvector only       | Separate vector DB (Qdrant)    | Operational simplicity, unified transactions                    | Embeddings >1M & perf regression                      |
| D-003 | 2025-08-15 | Local Ollama models              | Hosted APIs                    | Privacy, cost control                                           | Latency > targets with tuning                         |
| D-004 | 2025-08-15 | LoRA/QLoRA adapters              | Full fine-tune                 | VRAM constraints, faster iteration                              | Adapter underfitting critical tasks                   |
| D-005 | 2025-08-15 | Defer FastAPI endpoints          | Build early API                | Reduce scope & complexity                                       | Need multi-user or external tool access               |
| D-006 | 2025-08-15 | Materialized views for metrics   | On-demand heavy queries        | Performance predictability                                      | Staleness sensitivity or frequent incremental updates |
| D-007 | 2025-08-15 | Single config module             | Multiple config helpers        | Central validation & audit                                      | Scaling environment variants                          |
| D-008 | 2025-08-15 | Dependency pruning strategy      | Keep broad exploratory set     | Reduced footprint, clarity                                      | Missing capability blocks progress                    |
| D-009 | 2025-08-15 | Profile-first retrieval          | Raw-table prompts              | Higher grounding & brevity                                      | Profile maintenance overhead significant              |
| D-010 | 2025-08-15 | JSON logging                     | Plain text logs                | Machine parsability                                             | Disk pressure or readability issues                   |
| D-011 | 2025-08-15 | Next.js + TypeScript baseline UI | Streamlit, Panel, Dash, Reflex | Rich UX, long-term extensibility, direct access to JS ecosystem | Loss of single-language simplicity OR velocity drop   |

### 19.1 Pending decisions

- External scheduler selection (APScheduler vs Prefect) – defer until recurring automation volume > 3 distinct jobs.
- Polars adoption – pending profiling evidence of Pandas bottlenecks (CPU or memory) beyond thresholds.
- External ANN engine – pending embedding corpus size & latency triggers (see NFR scalability thresholds).

### 19.2 Decision hygiene

- Each new architectural decision recorded with ID, date, rationale, revisit criteria.
- Quarterly (or major milestone) review of decisions; stale items migrated to archive.

## 20. Repository scaffolding (greenfield)

### 20.1 Mono vs multi-repo

- Adopt single mono-repo with two top-level application roots:
  - `backend/` (FastAPI services, enrichment & LLM utilities) – Python only
  - `frontend/` (Next.js app)
- Shared artifacts (schema docs, models, prompts, decision log) live under `docs/`, `models/`, `prompts/`.
- Rationale: simplifies coordinated versioning & cross-layer refactors while team size = 1.

### 20.2 Top-level directory layout (proposed)

```
root/
  backend/
    app/
      api/                # FastAPI routers (modular by domain)
      core/               # Config, logging, settings, security utilities
      db/                 # Session management, migrations (alembic)
      models/             # SQLModel / Pydantic models
      services/           # Business logic (analytics fetch, enrichment triggers)
      enrichment/         # Enrichment pipeline stages (entity_resolution, embeddings, inference)
      retrieval/          # Profile & semantic retrieval utilities
      llm/                # Prompt templates, adapter selection, evaluation harness
      tasks/              # (Future) scheduler task definitions
      telemetry/          # Logging, metrics helpers
      scripts/            # One-off maintenance scripts (lightweight entrypoints)
    tests/
      unit/
      integration/
      enrichment/
    alembic/              # Migration env
    requirements.txt
    requirements-optional.txt
  frontend/
    src/
      app/ or pages/      # Next.js routes (dashboard, explorer, capabilities, uplift, ai)
      components/         # Reusable UI primitives & feature components
      features/           # Feature modules (state + data hooks + UI composition)
      lib/                # API client, schema validation, util functions
      styles/             # Global styles, design tokens
      hooks/              # Custom React hooks
      tests/              # Jest unit tests colocated by domain
      e2e/                # Playwright specs
    public/               # Static assets
    package.json
    tsconfig.json
    .eslintrc.cjs
  models/                 # Adapter weights (versioned folders), model cards
  datasets/               # Instruction & evaluation datasets (manifests only, large data gitignored)
  prompts/                # Prompt & template definitions (YAML/JSON)
  scripts/                # Cross-layer scripts (benchmark, audit)
  docs/                   # PRD, decision log, architecture diagrams
  benchmarks/             # Stored benchmark JSON outputs
  reports/                # Dependency audits, quality reports
  .env.example            # Documented environment variables
  .gitignore
  pyproject.toml (future) # Potential migration from requirements.txt
  Makefile (optional)     # Common task aliases (lint, test, build)
```

### 20.3 Naming & modularity guidelines

- Module names: lowercase, underscores for Python; kebab-case for directories in frontend if not Next.js enforced naming.
- Keep file size < 500 LOC; split by domain (e.g., `analytics_service.py`, `embedding_stage.py`).
- Avoid cyclic imports: service layer calls DAO/retrieval lower layer only.

### 20.4 Dependency boundaries

- `backend/app/enrichment` must not import from `frontend/`.
- `frontend/` consumes backend through generated API client only (no shared runtime Python–TS code; share via OpenAPI + JSON schemas).
- Shared constants (e.g., provenance codes) duplicated with generation script if necessary (future: generate TS enum from Python source).

### 20.5 Configuration

- Single `.env` at repo root; backend `config.py` loads & validates.
- Frontend environment variables prefixed `NEXT_PUBLIC_` for exposure; mirrored documentation in `.env.example`.
- Sensitive values never exposed to frontend (DB creds, model adapter path).

### 20.6 Database migrations

- Alembic environment configured under `backend/alembic` with autogenerate carefully reviewed (no blind auto merges).
- Migration naming: `YYYYMMDD_HHMM_<short_descriptor>`.
- Enrichment materialized view refresh scripts co-located; migration can include creation but refresh logic lives in service layer.

### 20.7 Testing strategy mapping

| Test Type           | Location                         | Scope Examples                              |
| ------------------- | -------------------------------- | ------------------------------------------- |
| Unit                | backend/tests/unit               | Win prob calc, parsing, small SQL utilities |
| Integration (DB)    | backend/tests/integration        | Materialized view query shape & latency     |
| Enrichment          | backend/tests/enrichment         | Incremental embedding selection logic       |
| Frontend unit       | frontend/src/tests               | Component rendering, hooks                  |
| E2E (Playwright)    | frontend/e2e                     | Dashboard load, explorer semantic search    |
| Performance (smoke) | benchmarks scripts + JSON output | Query p95, embedding throughput             |

### 20.8 Tooling & automation

- Root Makefile (or PowerShell script on Windows) shortcuts: `make setup`, `make test`, `make lint`, `make bench`.
- Pre-commit hooks (future) enforce format (black, isort), lint (ruff), type (pyright/mypy), frontend ESLint & Prettier.
- Scheduled (manual for now) script: `scripts/dependency_audit.py` updates `reports/dependency_audit.json`.

### 20.9 Git conventions

- Branch naming: `feat/<short>`, `fix/<short>`, `chore/<short>`, `docs/<short>`, `refactor/<short>`.
- Conventional commit messages (e.g., `feat(uplift): add action ranking rationale`) -> enables future changelog automation.

### 20.10 Data & large file handling

- Large raw datasets, intermediate dumps, and embeddings excluded via `.gitignore`; store path conventions documented.
- Optionally maintain `data/README.md` describing acquisition & refresh procedure.

### 20.11 Security hygiene

- `.env` present but `.env.example` lists every variable with doc comment (# description, default).
- Add `scripts/check_no_network.py` (future) scanning code for disallowed domains to enforce local-only policy.

## 21. Issue taxonomy & labeling

### 21.1 Labels (core set)

| Label               | Description                         | Color Suggestion |
| ------------------- | ----------------------------------- | ---------------- |
| `type:feature`      | New user-facing capability          | Blue             |
| `type:enrichment`   | Data enrichment / pipeline work     | Teal             |
| `type:ai`           | LLM, retrieval, prompts, evaluation | Purple           |
| `type:perf`         | Performance / optimization          | Orange           |
| `type:refactor`     | Internal code quality change        | Light gray       |
| `type:docs`         | Documentation updates               | Gray             |
| `type:test`         | Testing infrastructure or coverage  | Yellow           |
| `type:chore`        | Maintenance (deps, tooling)         | Neutral          |
| `priority:high`     | Must land for MVP acceptance        | Red              |
| `priority:medium`   | Important but can slip minorly      | Amber            |
| `priority:low`      | Nice-to-have / backlog              | Green            |
| `status:blocked`    | Awaiting dependency/decision        | Black            |
| `status:needs-spec` | Requires further elaboration        | Pink             |
| `nfr`               | Non-functional requirement work     | Brown            |
| `modernization`     | Dependency pruning / upgrade        | Indigo           |

### 21.2 Issue template pointers

Minimum fields for feature issue:

- Summary
- User Story reference (GH-###) or NEW if not yet in PRD (then add to PRD on merge)
- Acceptance Criteria (copy or refine)
- Technical Notes (queries, models, endpoints)
- Definition of Done (tests, docs, perf budget)

### 21.3 Epics & grouping

- Use GitHub Projects (future) OR milestone tags aligning to phases (Phase 1 .. Phase 5) (see Section 9.3).
- Epic naming pattern: `epic:strategic-dashboard`, `epic:enrichment`, `epic:ai-agent`, `epic:uplift-model`.

### 21.4 Cross-cutting concerns

- Performance tasks always link baseline metric & target metric.
- Modernization tasks cite dependency audit JSON entry.
- AI tasks reference adapter version or dataset manifest version when applicable.

### 21.5 Definition of Ready checklist

An issue is Ready when:

1. Acceptance criteria unambiguous & testable.
2. Data availability confirmed (or stub strategy documented).
3. Performance & privacy considerations noted (if applicable).
4. Dependencies (other issues/decisions) listed.
5. Rollback / failure mode outlined for risky changes.

## 22. Launch readiness checklist (MVP gate)

### 22.1 Functional completion

- [ ] All High priority user stories implemented (see Section 15).
- [ ] Manual exploratory test pass across all dashboard tabs & explorer.

### 22.2 Performance

- [ ] Dashboard median load ≤ 5s (measured 5-run average).
- [ ] p95 query latency logs within targets (Section 7.3 / 17.1).
- [ ] Embedding similarity lookup p95 < 500ms (sample 50 queries).

### 22.3 Quality & testing

- [ ] Statement coverage ≥ 60% core modules (analytics, enrichment, win probability).
- [ ] E2E Playwright scripts pass (dashboard load, explorer search, export flow).
- [ ] No critical accessibility violations (axe) on primary pages.

### 22.4 Data & enrichment

- [ ] Materialized views refreshed within last 24h.
- [ ] Enrichment provenance coverage ≥ 99.5%.
- [ ] Drift metric below alert threshold.

### 22.5 AI & LLM

- [ ] Adapter (if used) evaluation metrics meet thresholds (Section 16.6).
- [ ] Hallucination sampling daily run green 3 consecutive days.
- [ ] Provenance citation rate ≥ 90% in manual sample (n ≥ 20).

### 22.6 Security & privacy

- [ ] Static scan shows no prohibited outbound network code paths.
- [ ] `.env.example` updated & matches `config.py` expectations.
- [ ] Secrets not committed (git grep check).

### 22.7 Documentation

- [ ] README (new repo) includes setup, run, benchmarks instructions.
- [ ] PRD updated & version bumped (Section 1.1).
- [ ] Decision log current; no pending high-impact decisions unresolved.

### 22.8 Operations

- [ ] Benchmark JSON artifacts stored under `benchmarks/`.
- [ ] Dependency audit report present & < 35 direct deps.
- [ ] Recovery play: documented steps to rebuild DB & rerun enrichment from raw.

### 22.9 Sign-off

- [ ] Final review pass (self) documented with timestamp in CHANGELOG or release notes.

## 23. Post-launch operational playbook

### 23.1 Routine cadence

- Daily (when working): review logs for errors, drift alerts.
- Weekly: run dependency audit (if changes), refresh benchmarks, review performance deltas.
- Monthly: full enrichment re-benchmark, review decision log for revisit triggers.

### 23.2 Incident response (single-user adaptation)

- Severity levels:
  - Sev1: Data corruption risk (incorrect financial figures) – stop analysis, restore from last backup.
  - Sev2: AI hallucination spike (hallucination rate > target 2 consecutive samples) – revert adapter.
  - Sev3: Performance degradation (p95 > target +50% for 2 days) – profile & rollback recent perf-related commits.
  - Sev4: Minor UI or cosmetic issue – backlog if not user-blocking.

### 23.3 Backup & restore (local)

- Nightly (manual or scheduled) PostgreSQL dump of processed + enrichment schemas (`s2_interim`, `s3_processed`) stored compressed with timestamp.
- Model adapters & dataset manifests versioned (no binary overwrite).
- Restore order: DB -> materialized view refresh -> enrichment incremental catch-up -> adapter warm-up.

### 23.4 Performance regression handling

- Maintain rolling JSON of p50/p95 per key query (last 14 runs) – simple linear diff detection triggers warning if >20% regression.
- On regression: capture EXPLAIN ANALYZE, compare index usage, evaluate recent schema or code changes, document fix path.

### 23.5 Change management

- Every merged feature branch updates CHANGELOG (Keep a Changelog format) with Added/Changed/Fixed/Performance sections.
- Adapter deployment adds entry under "AI" subsection with metrics deltas.

### 23.6 Continuous improvement backlog seeds

- Automate enrichment batch incremental refresh scheduler (APScheduler spike).
- Graph-based capability gap recommender exploration.
- Replace heuristic uplift model with calibrated logistic regression (post pursuit history volume).
- Add structured evaluation harness for semantic search MRR / recall@K.

### 23.7 Decommission / archival

- Archive older enrichment batches & logs beyond retention (e.g., keep last 6 months) compressing JSON logs.
- Maintain manifest of archived artifacts for traceability.

---

End of document.

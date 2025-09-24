<!--
Technical Companion consolidating prior planning / architecture / agentic LLM / dataset / task / refactor docs.
Source docs merged: AGENTIC_LLM_PLAN.md, DATASET_AND_FINETUNE_PLAN.md, FRESH_CONVERSATION_CONTEXT_UPDATED.md (supersedes prior), PLANNING.md, TASKS.md, REFACTORING_SUMMARY.md, plus contextual elements from FRESH_CONVERSATION_CONTEXT.md. Excluded per instruction: CAPTUREINTEL.md (kept standalone) and PRD (kept standalone). Historical Streamlit references are normalized to Next.js direction per PRD v0.2. -->

# Technical Companion (Single Source of Truth – Architecture, AI, Operations)

Version: 0.1 (August 15, 2025)  
Status: Living document complementing `prd.md` (Product scope & user stories) and `CAPTUREINTEL.md` (capture intelligence data dictionary & Shipley mapping).

## 1. Purpose & Relationship to PRD

This companion centralizes all non‑product‑story technical material: current state snapshot, modular architecture, agentic LLM plan, dataset & fine‑tuning strategy, operational roadmap, refactoring outcomes, migration playbooks, and condensed task / phase status.  
Use it to: (a) stand up / extend the system, (b) onboard contributors, (c) guide AI & enrichment evolution.  
For functional requirements & acceptance criteria, defer to `prd.md` Sections 4–17. For detailed capture intelligence schemas & Shipley alignment, defer to `CAPTUREINTEL.md`.

## 2. Current Context Snapshot (Post-Migration)

Major milestone: Migration to official Python MCP SDK completed; legacy FastMCP & hybrid event loop instability removed.  
Operational foundations in place: PostgreSQL (multi‑schema), local Ollama LLM runtime, enrichment-ready ETL (raw→interim→processed), early agent tooling, refactored modular codebase trend.

Key Points:

- Python MCP database server (official SDK) provides 4 core tools: `get_database_schema`, `get_table_info`, `execute_sql_query`, `get_server_status`.
- Event loop “closed” errors resolved; pure Python async stack simplifies maintenance.
- Hardware baseline (64GB RAM, RTX 4060) adequate for 7B–13B quantized models + PEFT adapters.
- Strategic shift: Next.js + FastAPI architecture (Streamlit references now historical; UI modernization governed by PRD Section 8.8 & 10.30 stories).
- Domain gap identified: nuanced government contracting semantics (e.g., modification filtering) slated for domain fine‑tuning (LLM adaptation Phase 3, see Section 6).

## 3. High-Level Modular Architecture (Implementation View)

Layers (mirrors & extends PRD Section 8; normalizing older Streamlit planning):

1. Data Ingestion & Staging: Raw ingest (`s1_raw`), cleansing / normalization (`s2_interim`), dedup + analytics views (`s3_processed`).
2. Enrichment & Knowledge Layer: Entity resolution, text normalization, embeddings (pgvector), inferred attributes, profile/materialized views, clustering & drift monitoring.
3. Retrieval & Query Layer: Direct SQL (analytic views + materialized views) + semantic similarity (vector index) + profile-first retrieval heuristics.
4. API / Service Layer (evolving): FastAPI endpoints (metric bundles, explorer queries, profile retrieval, uplift calculation) — internal module calls allowed during early bootstrap.
5. Frontend (Next.js): Feature routes: dashboard, explorer, capabilities, uplift, ai (agent console). Shared component & design token system.
6. Agent Orchestration: MCP tool registry + agent graph (LangGraph deferred until advanced chaining). Capture Intelligence Agent consumes MCP tools + retrieval layer.
7. AI Adaptation Layer: Prompt templates, instruction dataset manifests, PEFT adapters (LoRA/QLoRA), evaluation harness, rollback mechanism.
8. Observability & Diagnostics: Structured JSON logs (queries, AI interactions, enrichment batches), drift metrics, benchmark artifacts.

Principles:

- Retrieval before model memorization (lean context injection, provenance enforcement).
- Incremental enrichment (changed rows only) to control compute.
- Single authoritative config module & environment gating.
- Materialized views for hot aggregates; manual refresh (scheduler deferred).

## 4. Data Pipeline & Schemas (Condensed)

Three-stage pattern (see PLANNING heritage):

- `s1_raw`: Source fidelity (no transforms)
- `s2_interim`: Type normalization, cleansing (still no heavy indexing)
- `s3_processed`: Deduplicated analytics tables, indexes, materialized views, precomputed filter & quarterly tables, vector columns, enrichment profile outputs.

Dedup Keys:

- Prime: `contract_transaction_unique_key`
- Subaward: composite (`prime_award_unique_key`, `subaward_number`, `subaward_action_date`)

Enrichment Artifacts (mapped to PRD user stories GH-067..GH-090):  
Entity resolution tables, normalized text columns (`*_clean`), embeddings, inferred attributes with confidence, requirement & company profile views, knowledge graph edge table, semantic clusters, enrichment batch log, drift metrics, override & provenance fields.

## 5. Agentic LLM Architecture (Operational Blueprint)

Phases (mapped & unified from AGENTIC_LLM_PLAN):

1. Foundation (Completed): Documented plan; MCP tool migration done; baseline agent stable.
2. Intent-Driven Backend Refactor: Tool router & structured intent schema (JSON) bridging natural language -> tool calls (GH-023..GH-027 alignment).
3. Dynamic Tool Selection Prompting: System prompt enumerates tool capabilities & schema snippet; Llama3.2‑8B primary, Mistral‑7B fallback.
4. Orchestrated Chaining: Multi-step reasoning (query → summarize → uplift) with intermediate state retention (Phase 2 of TASKS “Agentic Framework Optimization”).
5. Fine-Tuning & Adapter Rollout: Domain adapters (analysis vs narrative or unified with style tokens) using curated instruction dataset (Section 6).
6. Domain Specialization: Government contracting semantics (modification logic, NAICS adjacency, competition intensity heuristics) — reduces follow-up clarifications.

Structured Intent Output Examples (unchanged): data_query & visualization JSON patterns. Backend enforces whitelist and provenance insertion; ambiguous intents generate clarifying prompt.

Error Modes & Mitigations:

- Ambiguous fields -> agent returns clarifying question template.
- Missing embeddings -> fallback lexical ranking with warning tag.
- Oversized context -> summarization compression pass (target 10–15% token reduction) before generation.

Success Metrics (subset):  
Grounding ≥90%, Hallucination ≤5%, Median 512-token generation ≤2.5s, Citation accuracy ≥95%.

## 6. Dataset & Fine-Tuning Strategy (Consolidated)

Objectives: Improve instruction adherence, reduce hallucination, encode domain heuristics, optimize smaller local models via PEFT.

Data Sources & Inputs:

- Field semantics & glossary (`CAPTUREINTEL.md`, PRD Section 14).
- Enriched profile views & historical award records.
- Dashboard query logs / saved explorer configurations.
- Synthetic expansions (audited) for sparse intents.
- Abstracted Shipley patterns (non-proprietary derivatives).

Curation Pipeline (stages compressed): Ingest → Segment → Instruction synthesis → Deduplicate (cosine >0.92 removal) → Safety scrub → Token distribution QA (<3% truncation) → Stratified split → Quality sampling → Manifest & hashing.

Adapter Training Defaults: LoRA r=16–32, α=32, dropout=0.05, QLoRA (NF4 4-bit) to fit VRAM; cosine LR schedule (5e‑5..1e‑5 sweep) with early stop on composite score stagnation (grounding 50%, instruction adherence 30%, style conformity 20%).

Evaluation Harness: Computes grounding score, hallucination rate, citation accuracy, instruction adherence, latency; differentiates retrieval vs generation failure classes.

Governance: Dataset manifests + model cards versioned; rollback symlink pattern (`current_adapter` / `prev_adapter`); daily hallucination sampling (n=25) with alert threshold.

## 7. Operational Roadmap & Phase Alignment (Merged Planning + Tasks)

Macro Phases (superseding older multi-document lists):

1. Data & Performance Hardening (PRD Phase 1) – COMPLETE.
2. Strategic Dashboard Core Tabs – IN PROGRESS (Next.js implementation starting; Streamlit legacy retired).
3. Explorer & Capability Stance Module – PENDING.
4. AI Data Agent & Markdown Export – PARTIAL (agent base done; export pipeline next).
5. Projection, Uplift Modeling, QA Polish – FUTURE.

Agentic Sub-Phases (post MCP migration):
Foundation (done) → Tool Chaining & Performance → Domain Fine-Tune → Expanded MCP Tool Ecosystem → Full Capture Management Automation.

## 8. Condensed Task Status (High-Value Items Only)

Completed Highlights:

- ETL refactor with three-schema pipeline & dedup automation.
- MCP migration (official SDK) + stabilized async.
- Competitive analysis visualizations (legacy implementation reference – to be ported).
- GitHub MCP tool integration (foundation for multi-tool suite).

Active / Near-Term Priorities:

- Re-platform UI to Next.js baseline (PRD GH-111..GH-115).
- Implement FastAPI metric bundle endpoint & schema validation.
- Tool router + structured intent schema (Agent Phase 2).
- Export pipeline (Markdown capture profile with provenance & AI sections).
- Uplift model heuristic prototype (GH-051..GH-055).
- Embedding & enrichment incremental job instrumentation (GH-069, GH-075).

Deferred (Track in Backlog): External data sources (SAM.gov live ingestion), advanced clustering-based opportunity grouping, scheduler integration (APScheduler vs Prefect), advanced observability (Langfuse self-host).

## 9. Refactoring & Migration Summary (Unified)

Refactoring Outcomes:

- Centralized MCP client management eliminated manual JSON-RPC & scattered async handling.
- Simplified agent & chat interface; reduced duplication.
- Error handling standardized (graceful degradation + logging).
- Legacy hybrid stack elements scheduled for removal (ensure no orphan imports before deletion).

Migration Playbooks:
| Migration | Driver | Key Steps | Success Criteria |
|-----------|--------|-----------|------------------|
| FastMCP → Python MCP SDK | Stability, simplicity | Implement server, replace client, update agent, remove hybrid deps | No loop errors; all 4 tools operational |
| Streamlit → Next.js | UX scalability | Scaffold Next.js shell, port metrics/filters, replace AgGrid with React Data Grid, align design tokens | Dashboard shell LCP ≤2s, parity metrics |
| Adapter Rollout (LLM) | Domain reasoning | Train LoRA, evaluate, deploy via Ollama custom model | Eval thresholds met, rollback path valid |

## 10. Performance & Quality Guardrails (Extracted + Actionable)

Key Targets (see PRD Sections 7 & 17 for exhaustive list):

- Filtered dashboard load ≤5s median; p95 ≤7s.
- 512‑token generation p95 ≤2.5s (tuned 7B) with retrieval context.
- Similarity lookup p95 <500ms corpus<1M; revisit architecture beyond thresholds.
- Enrichment batch (≤5% change) <10m; profile view refresh single target <2s median.

Regression Monitoring: Benchmarks JSON updated post significant dependency or adapter change; alert if p95 regression >20% for two consecutive runs.

## 11. Risk Register (Condensed)

| Risk                                | Impact                      | Likelihood | Mitigation                                                | Trigger to Escalate        |
| ----------------------------------- | --------------------------- | ---------- | --------------------------------------------------------- | -------------------------- |
| Embedding latency growth            | Slower semantic search      | Medium     | Monitor p95; switch to external ANN upon threshold breach | p95 >700ms                 |
| Domain misunderstanding (mod logic) | Incorrect analytics answers | High (now) | Domain fine-tune + rule injection                         | >10% clarification rate    |
| Stale materialized views            | Misleading metrics          | Medium     | Refresh controls + staleness badge                        | >24h age detected          |
| Adapter overfitting                 | Hallucination rise          | Low        | Eval harness, daily sampling                              | Hallucination >5%          |
| Schema drift                        | Pipeline break              | Medium     | Automated schema diff & migration utility                 | Drift alert unresolved 48h |

## 12. Governance & Versioning

Artifacts & Locations:

- Product scope: `docs/prd.md` (versioned header).
- Technical companion: this file (increment minor on material structural change).
- Capture intelligence dictionary: `docs/CAPTUREINTEL.md` (independent updates).
- Dataset manifests: `datasets/manifest.json` (hash-verified).
- Model cards: `models/model_card_<version>.md`.

Change Workflow:

1. Update source sections (avoid duplicating PRD content).
2. Adjust cross-references (Section numbers stable).
3. Increment version & summary in changelog (future).
4. Run benchmark & hallucination sample on adapter-affecting changes.

## 13. Appendices

### 13.1 Mapping of Retired / Merged Documents

| Former Document                 | Status     | Replacement Section(s) |
| ------------------------------- | ---------- | ---------------------- |
| PLANNING.md                     | Merged     | Sections 3,4,7,8,10    |
| TASKS.md                        | Condensed  | Sections 7,8,9         |
| AGENTIC_LLM_PLAN.md             | Merged     | Sections 5,6           |
| DATASET_AND_FINETUNE_PLAN.md    | Merged     | Section 6              |
| FRESH_CONVERSATION_CONTEXT\*.md | Superseded | Section 2              |
| REFACTORING_SUMMARY.md          | Merged     | Section 9              |

### 13.2 External References

Consult PRD Sections:

- 8 (Technical considerations) for deeper stack rationale.
- 10 (User stories) for implementation acceptance.
- 16 (LLM strategy) for additional fine-tuning KPIs.
- 17 (NFRs) for exhaustive performance/security criteria.

### 13.3 Glossary Delta

Glossary lives in PRD Section 14; new term additions since PRD v0.2:

- Structured Intent Schema: JSON envelope produced by orchestrator LLM describing requested tool actions (fields: intent, filters, projections, chart spec).
- Tool Router: Backend component translating structured intent into validated tool invocations with provenance injection.

---

End of Technical Companion v0.1

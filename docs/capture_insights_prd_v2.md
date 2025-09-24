# PRD: Capture Insights Platform

## 1. Product Overview

### 1.1 Document Title & Version

- Title: Capture Insights Platform – Product Requirements Document (PRD)
- Version: 0.1 (In-Progress Draft – August 18, 2025)
- Status: Draft (Sections 1–2 only; technology stack & detailed specifications to be iteratively appended)
- Owner: (You – acting as Product, Engineering, Capture Manager)

### 1.2 Product Summary

Capture Insights is a local, private tool that helps you move quickly from raw federal contract data to clear decisions about whether and how to pursue an opportunity. It pulls processed historical award data (prime and subaward) into simple dashboards, lets you explore competitors and upcoming recompetes, builds and maintains a reusable baseline of your company capabilities, and uses local AI to draft win themes and narrative blocks. Everything runs on your own machine. No outside AI services. No hidden network calls.

The heart of the product is the "capture loop":

1. Pick and filter a slice of the market.
2. See core spend, timing, and competitor signals fast.
3. Spot expiring or likely-to-recompete contracts.
4. Compare your capability baseline to requirements, incumbents, and other competitors.
5. Generate data‑backed win themes and action ideas.
6. Export a clean Markdown capture profile with sources.

The product stays lean on purpose: fewer screens, faster answers, lower mental load. Advanced features (multi-user, heavy automation, external SaaS integrations) wait until the single‑user workflow is rock solid.

### 1.3 Problem Statement

Early capture work today usually means jumping between spreadsheets, clunky downloads, and manual notes. That wastes time, buries context, and makes it hard to repeat what worked. Data is often too summarized to be useful or too raw to be quick. There is no simple, private workstation tool that: (a) shows the right market and competitor slices fast, (b) keeps a living baseline of what your company can actually do, and (c) helps draft trustworthy narrative content with clear source references.

### 1.4 Vision Statement

Be the go‑to local workbench that lets a capture manager get from “What is really happening in this slice of the market?” to “Here is our positioning and plan” in one focused session—always with traceable sources.

### 1.5 Guiding Principles

1. Local & Private: Runs fully on your machine; nothing leaves it.
2. Source Traceability: Every number and AI statement links back to a table, view, or rule.
3. Capability Baseline First: Keep an always-current view of what the company can deliver; reuse it everywhere.
4. Less Surface, More Signal: Only add screens or toggles if they cut real time or increase clarity.
5. Fast Feels Better: Filtered dashboard responses in under 5 seconds guard user focus.
6. Export Early & Often: The capture profile is a first-class output, not an afterthought.
7. Modular by Default: Data ingest, enrichment, analytics, AI, and export remain cleanly separated.
8. Measurable Change: Each feature must claim (and later prove) a time, quality, or accuracy gain.
9. Plain Language: Use clear terms instead of jargon—opt for “source link” over “provenance,” etc.
10. Reuse Before Build: Prefer composing or lightly adapting existing open-source Model Context Protocol (MCP) servers / tool snippets over writing bespoke code from scratch.
11. Explorer-First: Minimize required setup steps and commands—the user should discover and refine, not babysit infrastructure.
12. Zero Incremental Cost: Favor free, local, open-source components; no paid SaaS dependencies in MVP.

### 1.6 Capability Stance Focus & Data Sources

The capability stance (your company’s structured list of what it does: core, differentiator, emerging) is the anchor for every comparison:

- Company vs contractual requirement fit.
- Company vs incumbent strengths and gaps.
- Company vs broader competitor field.

How it is built and enriched:

1. Internal Historical Signals: Prime awards and subawards history supply recurring service areas, scope descriptors, set-aside patterns, and performance breadth.
2. Contract Artifacts (External, Targeted): Archived or inactive SAM.gov documents (e.g., PWS, solicitations) fill description gaps where award data is sparse.
3. Entity & Company Lookups: SAM.gov entity search enhances basic profile facts (size status, socio-economic flags, core registration data).
4. Open Web Snapshots (Carefully Scoped): Targeted web or public social signals (e.g., X.com feed summaries) add recent focus areas or emerging capability claims.

All external fetches are explicit, logged, and optional. If an external source is unavailable, the system still functions with internal historical data—marking enriched fields as “not yet enhanced.”

#### 1.6.1 How the Capability Stance Is Derived (Logic Overview)

The stance is not a hand-written marketing list; it is built (then optionally edited) from evidence. The platform walks through a consistent logic:

1. Reconstruct Work Actually Performed

   - Pull prime award records your company held (including modifications) and parse descriptions, PSC/NAICS, set‑aside flags, and period of performance.
   - Normalize noisy description text (lowercase, de-dupe near duplicates, strip boilerplate).
   - Cluster or group recurring phrases (e.g., “facility O&M,” “preventive maintenance,” “energy efficiency audits”) to surface real service themes.
   - Map those themes to preliminary capability tags (core candidates).

2. Quantify Self-Performance vs Subcontract Reliance

   - Join prime award obligations to associated subawards to calculate: total prime obligation, subcontracted dollars, subcontracted percent.
   - Flag awards with high subcontract percentage (e.g., >30% or configurable) for deeper review.
   - Capture which capability themes appear predominantly in subcontracted portions (possible internal gaps or strategic outsourcing).

3. Interpret Subaward Purpose (Gap vs Goal Fulfillment)

   - For each subaward: read its description + the recipient’s profile (when available) to classify why it likely existed:
     a. Skill / Capability Gap Fill (specialized labor or niche technical scope)
     b. Socio-Economic or Set-Aside Goal (e.g., SDVOSB, WOSB participation)
     c. Capacity Augmentation (same capability, scaling labor volume)
   - Heuristics: unique niche keywords (e.g., “cyber hardening assessment”) → gap fill; presence of socio-economic designation + generic labor phrasing → goal fulfillment.
   - Store rationale code with each inferred classification so it can be audited or overridden.

4. Drive Tool / Data Pull Selection for Enrichment

   - When a subaward recipient (or incumbent prime) lacks enough descriptive depth locally, the system chooses enrichment steps:
     - Web Search (public web snapshot) if company name + domain not yet profiled.
     - SAM.gov Entity API if registration / socio-economic flags are missing or stale.
     - Social Feed (e.g., X.com summary) if recent focus areas may influence emerging capability tags.
   - Selection heuristic example (plain language): “If we don’t have a capability summary paragraph AND we haven’t pulled SAM.gov data in the last 30 days, call the SAM.gov entity lookup first; if still sparse, run a web search; if competitive relevance score high, also pull social feed.”
   - Each tool invocation is logged with: trigger reason, inputs, tool name, and resulting enrichment fields.

5. Model Incumbent & Competitor Capability Profiles the Same Way
   - Apply identical parsing and clustering to competitor prime awards (where available) plus any subaward records where they appear as recipients.
   - Trace their subcontract reliance ratio by capability theme to identify where they ALSO depend on niche partners (advantage parity) or where they self-perform strongly (potential differentiator for them / gap for you).
   - If a competitor frequently subcontracts a theme you self-perform, mark that as a potential win theme angle (“We self-perform X that incumbent relies on subs for”).

#### 1.6.2 Classification & Tag Lifecycle (Human Readable)

Below is the same lifecycle expressed in plain language (pattern: Bold stage name → what happens → why it matters / outcome).

- **Extract**: Pull raw award and subaward description text, normalize (lowercase, strip boilerplate, de‑dupe near duplicates) and tokenize.

  - Outcome: Clean working corpus (noise reduced) so later clustering isn’t skewed by formatting or repeated boilerplate.

- **Group**: Aggregate frequently recurring and semantically similar phrase fragments into provisional clusters using simple frequency + similarity heuristics.

  - Outcome: Candidate thematic clusters that reflect real work patterns instead of one‑off phrasing quirks.

- **Label**: Add business meaning by mapping each cluster against NAICS / PSC context and curated keyword hints to generate an auto draft capability tag.

  - Outcome: Draft tags (machine-suggested) aligned to recognizable capability taxonomy anchors.

- **Validate**: Present draft tags in the stance editor so the user can approve, rename, merge duplicates, or discard weak/noisy ones; assign class (core / differentiator / emerging).

  - Outcome: Curated, classification‑rich approved tag list you can trust in comparisons and narrative generation.

- **Enrich** (optional, targeted): Call external enrichment tools (archived solicitations, SAM entity lookup, web snippets) only where descriptive depth is low to add concise evidence sentences.

  - Outcome: Enhanced tag metadata and stronger summary sentences without overfetching or diluting signal.

- **Version**: After any approve / merge / reclassify action, snapshot the approved set (sorted), hash it, and store timestamp + counts.
  - Outcome: Immutable stance revision record enabling audit, rollback reasoning, and consistent downstream AI prompt context.

#### 1.6.3 Data Quality & Fallback Behavior

- If subaward detail is missing, mark subcontract rationale = “unknown” (do not guess) and queue for enrichment.
- If enrichment tools fail (network, rate limit), skip gracefully and label needed fields “not yet enhanced.”
- If clustering produces overlapping themes (similarity above threshold), prompt user merge suggestion.
- Every auto-generated tag keeps a confidence score (simple: frequency weight × description richness factor).

#### 1.6.4 Why This Matters

This approach keeps the stance:

- Evidence-based (derived from what you and competitors actually did).
- Comparable (same extraction logic for you and others).
- Actionable (subcontract ratio + rationale directly feeds gap closure planning & win themes).
- Extensible (new data sources just add enrichment fields without reworking the core pipeline).

#### 1.6.5 Future Enhancements (Deferred)

- Lightweight semantic similarity model to refine cluster boundaries (only if basic TF/phrase grouping proves noisy).
- Adaptive thresholds tuned by feedback (e.g., reduce false split of near-identical capability tags).
- Cross-award temporal trend view (“capability X emerging over last N quarters”).
- Confidence-driven UI ordering (high confidence tags surfaced first in stance editor).

#### 1.6.6 Historical + External Data Consolidation & Column Inventory

Below is a practical picture of what “fully used historical data + targeted external enrichment” means before we summarize, embed, and enable semantic search. Think of it as building a rich, auditable paragraph for each award (and each subaward) from layered sources. Everything starts with what you already have; external pulls only fill gaps.

Prime Awards (Base + Enriched Fields – Human Readable)

- award_id_piid: Stable unique identifier used for joins & provenance; lets any number in UI link back to original row.
- prime_award_base_transaction_description: Raw base transaction text (initial evidence before cleaning/clustering).
- transaction_description: Modification-level text (only kept if meaningfully different from base) to add nuance.
- naics_code / naics_code_description: Structured industry code + readable label (augmented once, then cached) feeding tagging & filters.
- product_or_service_code / product_or_service_code_description: PSC code + enriched label providing mission / functional flavor.
- sam_gov_solicitation_descriptions (NEW): Extracted paragraphs from archived solicitations/PWS; fills sparse award narratives; boosts clustering quality.
- misc_external_descriptions (NEW): Curated short web/news/social snippets (strict cap) adding recency or differentiator hints.
- capability_tags_draft: Machine-extracted candidate thematic tags pending human validation.
- capability_tags_final: Curated approved tags (core / differentiator / emerging) driving comparisons & AI prompts.
- subcontract_reliance_flag: Boolean marker (e.g., high subcontract % threshold) signaling a gap or reliance area.
- data_enrichment_status: Enum (base_only / partial / enriched) for quick completeness filtering & enrichment targeting.
- embedding_vector: Dense numeric vector (local model) enabling semantic search & retrieval augmentation.
- summary_paragraph: Deterministic + optionally LLM-refined plain-language summary used in UI, export, and as embedding input.

Subawards (Base + Enriched Fields – Human Readable)

- subawardee_name / subawardee_uei: Recipient identity keys for entity resolution & graph linkage.
- subawardee_parent_name / subawardee_parent_uei: Parent roll-up fields supporting consolidation & dependency analysis.
- subaward_description: Original purpose text; primary signal for subcontract rationale inference.
- subaward_amount: Dollar magnitude feeding subcontract ratio & reliance computations.
- subawardee_sam.gov_description (NEW): Official registration-style summary adding formal capability framing.
- subawardee_external_descriptions (NEW): Recent web/social snippets highlighting emerging focus areas (bounded for noise control).
- inferred_subaward_rationale: Categorical classification (gap_fill / goal_fulfillment / capacity / unknown) guiding gap vs strategic outsource logic.
- rationale_confidence: 0–1 score prioritizing human review of weaker inferences.
- subcontract_capability_themes: Tag list tied specifically to subcontract scope (helps differentiate outsource pattern vs broad stance strength).
- enrichment_status: Same tri-state completeness marker as primes for pipeline monitoring.
- embedding_vector: Semantic representation enabling queries like “niche cyber subcontractors” or “energy audit partners.”
- summary_paragraph: Consolidated subaward narrative (clean + optionally enriched) powering retrieval & export context.

<!-- Removed redundant tabular version of Subawards fields; retained single human-readable bullet list above for clarity and to reduce duplication. -->

Enrichment & Summarization Flow (Plain Language)

1. Gather base columns (historical). If a prime award already has rich description text length > threshold, external description fetch may be skipped unless user forces.
2. Look up NAICS and PSC descriptions locally (cached) or fetch from authoritative sources once, then cache.
3. If description coverage score is low (short length, low unique token count), attempt SAM.gov solicitation retrieval (archived docs) → extract core paragraphs (regex + simple section heuristics: performance work statement, scope, objectives).
4. If still sparse OR flagged as emerging strategic area, run web/news/social enrichment (bounded number of snippets with max char limit each to avoid noise).
5. Merge text blocks in deterministic order: [base transaction(s)] + [solicitation excerpts] + [external snippets]. Deduplicate sentences by similarity threshold.
6. Generate a concise summary_paragraph (rule template first; optional LLM refinement locally, capped tokens, with strict prompt to preserve source facts only).
7. Extract / update draft capability_tags via phrase frequency + PSC / NAICS alignment + curated keyword list.
8. Join subawards, compute subcontracted percent. If > threshold and linked themes appear mostly in subcontracted portion, mark candidate internal gap.
9. Classify each subaward rationale (gap fill, goal fulfillment, capacity). Attach confidence.
10. Produce embedding_vector from the consolidated, clean summary (strip stop words but retain technical terms). Store in pgvector index.
11. Mark enrichment_status. Log what tools were called and why.

Semantic Search Pipeline (Award or Subaward – Human Readable)

1. Normalize: Clean + dedupe + sentence-split raw + enrichment text into canonical sentences (stable input surface).
2. Summarize: Apply rule template; optionally refine locally with LLM (strict factual prompt) to produce concise summary_paragraph.
3. Embed: Turn summary + key metadata tokens (NAICS, PSC tags) into vector (local embedding model) for similarity matching.
4. Index: Upsert vector + IDs into pgvector so the record becomes searchable.
5. Query: Convert user natural language query to vector; compute cosine similarity → preliminary ranked list.
6. (Optional) Rerank: Apply light heuristics (freshness boost, match density) to finalize order for UI display.

MCP Tool Context Strategy

- When an MCP tool (e.g., web_search, sam_entity_lookup) is invoked, it receives only the minimal necessary context: entity name, UEI, and specific missing fields; not the entire record blob.
- After tool completion, a merge function updates only the enrichment columns and recalculates description coverage score.
- Audit log entry: {tool_name, trigger_condition, entity_id, added_fields, duration_ms}.

Quality Safeguards

- Hard cap on external snippet count (e.g., 3) and characters per snippet to avoid dilution and embedding drift.
- Deterministic merge order ensures embedding stability across runs.
- Change hash (SHA256 of concatenated text blocks) stored; if unchanged, skip re-embedding.

Why This Matters for Capability Stance

- Tag accuracy improves because summaries blend structured codes + real descriptive language + external clarifiers.
- Gap inference is evidence-based: subcontract ratios + rationale codes, not gut feel.
- Semantic search can answer nuanced prompts (“past facility energy optimization with high subcontract reliance”) because those attributes are embedded together.

#### 1.6.7 Subaward Relationship Network & Lead Generation Logic

Beyond point‑in‑time capability inference, the history of who you subcontracted TO and who subcontracted TO YOU forms a relationship graph that feeds proactive lead generation (where to prime vs where to pursue as a strategic subcontractor).

Core Concepts

1. Role Perspective: Every relevant award viewable as (a) you-as-prime with outgoing edges to subawardees, or (b) you-as-sub on another prime’s contract (incoming edge from prime to you). Both matter.
2. Relationship Edge: (prime_entity -> sub_entity) with weighted attributes (total_dollars, percent_of_award, capability_theme_set, rationale_mix, recency_score).
3. Strength Score: f(dollar_share, recurrence_count, theme_diversity, recency) scaled 0–1; used to surface “strategic partners.”
4. Transition Candidate: A capability theme where you have repeatedly contributed as a sub but also self‑perform similar work elsewhere as prime (signal to pursue priming in that niche on recompete).
5. Teaming Opportunity: A prime that (a) contracts in themes you cover strongly, (b) shows increasing subcontract dependence in those themes, and (c) has upcoming expirations or large recompete windows.

Additional Derived Fields (Proposed – Human Readable)

- relationship_role (prime / sub): Indicates whether the record reflects you acting as prime or as sub; used for filtering and analytics splits.
- partner_entity_name: Counterparty name for the edge (prime ↔ sub) – becomes the graph edge label.
- partner_entity_uei: Counterparty UEI; stable key for joins and deduplication.
- partner_parent_name: Parent organization grouping; supports roll‑up aggregation.
- relationship_strength_score: 0–1 score weighting dollar share, recurrence, theme diversity, recency; drives partner prioritization (lead triage).
- unique_capability_themes_shared: Count of distinct capability themes shared on this edge; signals teaming rationale depth.
- sub_rationale_mix: Distribution of rationale categories (gap_fill / goal_fulfillment / capacity) for subs you issue; guides insource vs continue outsource decisions.
- recurrence_count: Number of distinct awards forming this edge; higher implies stability.
- last_active_fy: Most recent fiscal year the relationship was active; supports recency filters.
- transition_candidate_flag: True when you were a sub for a theme but have increasing self‑perform evidence elsewhere; feeds prime transition pipeline.
- partner_dependency_flag: True when high reliance on a specific sub is detected (risk & potential internal build signal).

Network Metrics & Use Cases

- Partner Portfolio Breadth: count(distinct partner_entity_name) by FY → shows diversification.
- Capability Reliance Map: heatmap (capability theme × role) with dollars & % subcontracted.
- Transition Radar: list of themes where (sub_role_dollars > threshold) AND (self_perform_dollars rising) AND (competitor incumbents show higher subcontract reliance) → probable upgrade targets.
- Teaming Target Shortlist: top N primes where your past sub work overlaps with their expiring vehicles and your stance shows core strength.
- Reciprocity Insight: identify partners who are BOTH your subs and your primes in different themes (potential strategic alliance vs diffuse dependency).
- Social Expansion Angle: highlight partners with high relationship_strength_score but low capability overlap diversity (opportunity to widen scope).

Lead Generation Workflow (Plain Language)

1. Filter by target agency / NAICS slice.
2. Inspect “You as Sub” tab: see primes you supported; flag those with upcoming expirations (based on contract end dates minus window).
3. Click a prime row → side panel shows: shared themes, subcontract rationale mix, your stance strengths not yet utilized.
4. “Promote to Prime Opportunity” button drafts a narrative: why you can prime similar work (self-perform evidence + competitor reliance).
5. In parallel, evaluate “You as Prime” dependency list: high partner_dependency_flag edges → decide build vs maintain strategic sub.
6. Export updated capture profile section: includes partnership map summary and top 5 transition candidates.

Graph Construction & Refresh

- Batch job (or manual trigger) constructs edge list from unified prime + subaward tables.
- Edge weight recalculated only if: new award added, modification above dollar delta threshold, or enrichment fields updated (to avoid churn).
- Lightweight in-memory graph (NetworkX or custom) → precompute centrality (degree, weighted betweenness) only for active slice.

Semantic Layer Integration

- Relationship summaries (edge-level) are embedded too, enabling queries like: “partners specializing in energy audits we relied on the most last 3 years” or “primes we subbed for in cyber that have contracts expiring next FY.”

Risk & Mitigation

- Sparse Subaward Data: If subaward reporting incomplete, mark reliability tier; do not overfit conclusions (badge: “limited subaward coverage”).
- Over-Clustering Partners: Keep parent vs subsidiary awareness; do not auto-merge without parent_uei confirmation.

Outcome Benefits

- Direct feed into action lists (prime vs sub strategy).
- Early warning on over-concentration (too much dependence on single niche partner).
- Clear, data-backed rationale paragraphs for teaming outreach emails (auto-drafted local).

### 1.7 Technology Stack (MVP, Shipley-aligned)

All design choices below are optimized for Shipley-style business development and capture management workflows: get to qualified insights quickly, maintain a defensible position with sources, and generate win themes and capture artifacts with minimal ceremony.

- Primary language: Python 3.12+

  - Tooling policy: prefer uv over pip for speed, reproducibility, and Python version management.
  - Style: PEP8, type hints, Black; Pydantic models for validation.

- Frontend: Streamlit

  - Rationale: single-file ergonomics, fast iteration, multipage navigation, native caching, test harness support.
  - Usage: dashboards for filters, tables, charts; chat elements for AI interactions.

- AI/Agents (local, open-source, free)

  - Ollama for local LLM inference and embeddings (Windows + NVIDIA 4060 GPU)
    - Target models for 8 GB VRAM class: Llama 3.2 8B Instruct (q4_K_M), Mistral 7B Instruct (q4_K_M), Qwen2.5 7B Instruct (q4_K_M).
    - Endpoints used: /api/chat for reasoning, /api/embed for semantic search.
    - JSON mode for structured outputs where appropriate.
  - PydanticAI (structured agents)
    - Purpose: strongly-typed tool use, schema-validated outputs, safer prompts for Shipley artifacts (win themes, gate checklists).
  - LangChain + LangGraph
    - Purpose: lightweight chains for retrieval + reasoning; LangGraph for explicit step control (e.g., data fetch → summarize → compare incumbent vs self → draft win themes).
  - Model Context Protocol (MCP) Python SDK
    - Purpose: define local tools/servers (web intelligence scraper, document creator/editor, visualization, analysis/reasoning) with narrow, auditable inputs.
  - VS Code AI Toolkit
    - Purpose: local agent development, prompt iteration, MCP tool wiring, optional model conversion and playground; no cloud-required features.

- Database: PostgreSQL with pgvector

  - Rationale: robust filters + vector search; index for embeddings on awards, subawards, relationships, and summaries.

- Packaging & runtime

  - uv for project creation, dependency locking, and Python installs.
  - No paid SaaS. All execution local. External APIs are called directly from the workstation with user-owned keys.

- Hardware profile awareness
  - 64 GB RAM, NVIDIA RTX 4060 (8 GB VRAM typical). Prefer q4_K_M quantization and limited context (4k–8k) for fast response and multi-tool workflows.

### 1.8 Data Sources & API Integration (governed, local execution)

All integrations are purpose-scoped, logged, and optional. Where an API requires an API key, keys are stored in local secrets only.

- USAspending (no auth required for public endpoints)

  - Reference: https://api.usaspending.gov/docs/endpoints
  - Use: advanced search (POST) for awards/transactions, subawards, spending by NAICS/PSC/agency/time; award details; last updated dates.
  - Purpose: historical spend baselines, competitor shares, subaward patterns, expiring vehicles.

- SAM.gov Contract Opportunities API (v2)

  - Reference: https://open.gsa.gov/api/get-opportunities-public-api/
  - Endpoint: https://api.sam.gov/opportunities/v2/search (requires api_key)
  - Key filters: date window (postedFrom/postedTo mandatory), NAICS (ncode), PSC (ccode), set-aside codes, organizationName.
  - Purpose: upcoming/active opportunities, set-aside targeting, solicitation metadata and links.

- SAM.gov Entity Management API (v1–v4)

  - Reference: https://open.gsa.gov/api/entity-api/
  - Endpoints: https://api.sam.gov/entity-information/v4/entities (Public requires api_key; FOUO/Sensitive require system account and roles).
  - Purpose: entity profiles, UEI resolution, NAICS/PSC footprints, socio-economic flags; optional extract mode for JSON/CSV.
  - Rate limits: vary by account type (public/system/federal). Enforce local backoff and quotas.

- GSA Pricing Intelligence (CALC+/Quick Rate)

  - Reference: https://buy.gsa.gov/pricing
  - Purpose: ceiling labor rates (MAS) and BLS crosswalks for IGCE sanity checks and competitive pricing cues. Where a programmatic API is unavailable, scrape is explicitly disallowed—use published downloads or documented endpoints only when provided by GSA.

- BLS Public Data API (v2 preferred)

  - Reference: https://www.bls.gov/developers/
  - Endpoint (v2): https://api.bls.gov/publicAPI/v2/timeseries/data/
  - Purpose: inflation indices, wage trends, unemployment series; maintain a local knowledge base of series metadata.

- ILOSTAT (SDMX)

  - Reference guide (PDF): https://webapps.ilo.org/ilostat-files/Documents/SDMX_User_Guide.pdf
  - Purpose: international labor series where relevant to cost narratives; integrate via SDMX endpoints where permitted and cached locally.

- Web search (targeted)
  - Library: duckduckgo_search (queries are external but no proprietary AI). Use minimal snippets with strict char limits and source capture.
  - Purpose: recent public signals for competitors or partners; strictly bounded and logged.

Integration Rules (Shipley context)

- All external pulls are tied to explicit capture questions (e.g., “Confirm incumbent UEI and NAICS alignment”).
- Each fetch logs: tool, reason, parameters, duration, and added fields; source links are preserved for inclusion in capture profile exports.
- If an external source fails or exceeds quotas, the system degrades gracefully and annotates “not yet enhanced.”

### 1.9 Local LLM Strategy (8B class, reproducible outputs)

- Models

  - Default generalist: Llama 3.2 8B Instruct (q4_K_M via Ollama)
  - Alternate: Mistral 7B Instruct, Qwen2.5 7B Instruct
  - Embeddings: all-minilm or nomic-embed variants via Ollama /api/embed

- Usage patterns

  - Deterministic drafting: temperature ~0.2, seed fixed for spec artifacts; JSON mode for schema-bound outputs.
  - Context discipline: deterministic text merge → summary → embed; change hash gates re-embedding.
  - Tool calling: PydanticAI and LangChain tool specs map to MCP tool servers where possible.

- Fine-tuning (deferred unless necessary)
  - Unsloth for local LoRA/QLoRA on curated instruction datasets (capture narratives, win themes with sources).
  - VS Code AI Toolkit playground for quick A/B and prompt tuning; no cloud dependency required.

### 1.10 Installation & Ops (uv-first)

- Installation policy

  - Use uv to install Python (pin 3.12), manage venv, and sync dependencies.
  - Provide uv-friendly scripts for: database init, ETL, embeddings, dashboard run, and tests.

- Secrets & config

  - Store API keys only in local secrets (.env + config.py access layer). Never in code or logs.
  - Validate critical configuration on startup; fail fast with clear remediation messages.

- Telemetry
  - Local structured logs only (no external APM). Performance counters around fetch, LLM calls, and DB ops.

### 1.11 Shipley Alignment Notes (BD/Capture)

- Shipley capture phases: market intel → positioning → gate reviews → proposal. The platform focuses on pre-proposal capture: qualification (bid/no-bid), competitor analysis, customer hot buttons, and win themes.
- Win strategy scaffolds: translate stance vs requirement gaps, incumbent reliance on subs, socio-economic alignment, and pricing cues into concise win themes with source citations.
- Gate-ready artifacts: qualification worksheet, competitor snapshot, teaming rationale, IGCE sanity notes, and risk mitigations—exported in Markdown with filters, timestamps, and model/version.

### 1.12 Security & Compliance

- Local-first: No external AI services. Data egress only to requested public APIs. Optional MCP tools must respect the same boundary.
- Provenance: Every computed metric and AI statement links to an award/subaward row, API record, or rule.
- Licensing: Prefer Apache/MIT/BSD libraries. Verify model and dataset licenses are suitable for commercial internal use.

### 1.13 Implementation Notes (concise)

- Minimal KEEP set

  - Core: streamlit, pandas, numpy, sqlalchemy/sqlmodel, psycopg, pgvector, pydantic, pydantic-ai, langchain, langgraph, duckduckgo_search, httpx/requests, ollama (client), uvicorn/fastapi (for API layer where needed).
  - Dev/Test: pytest, black, ruff (optional), mypy (light).

- UI affordances

  - Persistent filters, one-click “Export Capture Profile,” “Promote to Prime Opportunity,” and “Draft Win Themes.”
  - Status containers for long tasks; cached resources for DB connections and LLM models.

- Performance
  - Avoid overfetch: cap snippets and summarization tokens; batch API calls with backoff; index critical DB joins.

---

## 3. How to Use This PRD to Drive a Spec‑Kit constitution.md

When generating a Spec‑Kit constitution, feed the following structured summary to a prompt (local, no cloud). This captures the essential constraints and choices from above in Shipley capture context.

Spec‑Kit Prompt Scaffold (for constitution.md)

- Name: “Capture Insights (Local BD/Capture Workbench)”
- Vision: Local, private Shipley-aligned capture workbench from filtering to export; traceable sources; subaward/relationship signals; fast dashboard (<5s per filter).
- Non‑negotiables: All‑local LLMs (Ollama), open‑source only, uv for installs, keys in .env, no cloud AI; works on 64 GB RAM + RTX 4060 (8 GB VRAM) with 8B models.
- Frontend: Streamlit multipage (filters, insights, relationships, export). Chat elements for AI drafting.
- Data: PostgreSQL + pgvector; ingest USAspending, SAM.gov (Opportunities v2, Entity v4), GSA Pricing (CALC+/Quick Rate), BLS API v2, optional ILOSTAT SDMX; web search via DuckDuckGo (bounded).
- AI/Agents: Ollama (chat + embed), PydanticAI (typed tools, structured outputs), LangChain/LangGraph (retrieval + control flow), MCP Python SDK tools (web intel, document, viz, analysis), VS Code AI Toolkit (local agent dev + prompt A/B). Unsloth (optional LoRA fine‑tune).
- Models: Llama 3.2 8B Instruct (q4_K_M) default; alternatives: Mistral 7B, Qwen2.5 7B; embeddings: all‑minilm. Deterministic modes for exports (seed, low temp, JSON mode).
- Security: local‑only processing, explicit API calls, full provenance, open licenses.
- Install/Run: uv pin 3.12, uv sync, streamlit run strategic dashboard; keys in .env; validate config on startup.
- Deliverables: stance editor, expiring/recompete list, competitor snapshot, teaming map, win themes, Markdown export with filters + sources.

This scaffold, plus the detailed sections 1.7–1.13 above, should give Copilot Agent enough input to populate the Spec‑Kit constitution with accurate modules, constraints, and success criteria.

## 2. Goals

### 2.1 Business Goals

(Primary stakeholder = you. Emphasis: speed, clarity, reuse.)

1. Build and keep a trusted, reusable capability stance baseline that is referenced in ≥90% of comparative views (requirement fit, competitor comparison, export sections).
2. Cut time from “data refreshed” to “first draft capture profile” by ≥60% (target ≤30 minutes from focused filtering to export).
3. Reach ≥80% structural consistency across exported profiles (same core section order, required metadata) to reduce manual cleanup.
4. Achieve ≥70% acceptance (no or light edits) of AI-generated win themes by the end of iteration cycle 3.
5. Add a new governed data source (e.g., SAM.gov artifact fetch) in ≤2 concentrated development days using existing module seams.
6. Keep runtime lean: cold start to usable dashboard ≤90 seconds; direct production dependency count (KEEP set) ≤35.
7. Maintain full source trace links enabling later fine-tuning dataset extraction without retrofitting.
8. Maximize Reuse: Implement ≥70% of agent / tool capabilities by configuring or adapting existing MCP server patterns or open snippets (average custom code per new tool ≤150 lines) while keeping external service spend at $0.

### 2.2 User Goals (Capture Manager – Solo MVP)

1. Frame the Market Fast: Apply filters (agency / NAICS / PSC / time) and see key numbers in under 5 seconds.
2. Spot Recompetes: List expiring base contracts (6–24 months) with sortable value and timing signals.
3. Know the Competition: View top competitors, their share, concentration, and notable capability claims quickly.
4. Use Capability Baseline Everywhere: Reuse a single maintained capability list when comparing to requirements, incumbents, or other competitors.
5. Fill Description Gaps: Pull optional external artifacts (PWS, solicitations, entity lookups) when award text is thin—clearly labeled as enriched.
6. Semantic Find: Use natural language to surface similar awards or descriptions when structured filters are not enough.
7. Draft Faster: Generate win themes and snapshot narratives that need ≤20% edits before export.
8. Export with Confidence: Produce a consistent Markdown profile with exact filters, timestamps, model name, and source links.
9. Understand Every Number: Expand any metric or heuristic score to see the simple formula and any fallback assumptions.
10. Stay in Flow: Simple navigation, persistent filters, inline help—no surprise states.
11. Trust Local Operation: Visual indicator confirms everything is running locally with no unexpected outbound calls.
12. Be an Explorer, Not an Operator: Leverage conversational or lightweight command-style interactions to trigger data pulls, comparisons, or profile drafts without memorizing schema or internal tool names.

### 2.3 Non-Goals (MVP & Near-Term Deliberate Exclusions)

1. Multi-User Authentication / RBAC: Single trusted local user only; no session management complexity.
2. Full Proposal Lifecycle Management: No pipeline CRM, teaming workflow automation, or pricing models.
3. External Proprietary Platform Integrations (GovWin, Bloomberg Gov): Deferred until post-core value validation.
4. Real-Time Streaming Updates: Batch or on-demand refresh only; no continuous ingestion daemons initially.
5. Automated Complex ML Modeling Beyond Heuristics: Win probability = transparent weighted heuristic (not a black-box ML classifier) until sufficient labeled outcomes exist.
6. High-Fidelity Document Rendering (DOCX/PDF): Markdown export only (future conversion pipeline optional).
7. Large-Scale Distributed Compute: Single-node processing; no Kubernetes, Spark, or cluster orchestration.
8. Heavy Geospatial / 3D Visualization: Defer advanced mapping layers (no pydeck / deck.gl usage in MVP).
9. External APM / Hosted Telemetry: No third-party observability SaaS; structured local logs only.
10. Fully Automated Agentic Orchestration Graphs: Initial AI interactions are guided tools & templates; complex multi-step autonomous graphs postponed.
11. In-Browser Real-Time Collaboration: No shared editing or WebSocket presence features.
12. Automated Fine-Tuning Pipelines: Model adaptation (LoRA/QLoRA) gated behind stable prompt + data schema maturity.
13. Complex Workflow Scheduling UI: Manual script triggers; scheduling layer (APScheduler/Prefect) deferred.

---

(End of initial draft scope prior to adding the technology stack. Technology Stack & Architecture Choices now follow as Section 3. Personas will be drafted next as Section 4.)

## 3. Technology Stack & Architecture Choices (Draft)

This section translates principles into concrete, lean technology choices that match your single‑user, local, private focus while giving a clean runway for later evolution (multi‑user, scale, richer UI) without re‑platforming. It explicitly calls out: Adopt Now, Prepare, Defer.

### 3.1 Hardware Baseline (Human Readable)

- CPU – Intel Core i9‑14900HX (many cores + strong single thread): Enables fast local ETL and parallel text processing for clustering.
- GPU – NVIDIA RTX 4060 Laptop (~8GB VRAM): Supports 7B models full precision or 13B quantized (Q4_K_M); adequate for embeddings + light adapters.
- RAM – 64 GB (upgraded): Plenty for multi‑million row DataFrames, in‑memory caching of embeddings, and graph structures.
- Storage (NVMe SSD): Fast local I/O for Postgres data + streaming model weights with low latency.
- Display (2560×1600 @165Hz): High resolution helps present dense analytical UI panes without clutter.

Design Strategy: Stay single‑node, memory‑resident for intermediate transforms; avoid premature distributed systems. All components must gracefully run within laptop thermals (batch jobs chunked, optional GPU use).

### 3.2 Language & Runtime Strategy (Human Readable)

- Primary Language: Python 3.12.x (stable; broad library support; avoids beta C‑extension surprises).
- Upgrade Path: Prepare test matrix for Python 3.14 (free‑threaded opt‑in, deferred annotations PEP 649, template strings) after dependency readiness.
- Packaging / Env: Use `uv` for fast, reproducible installs (retain `pip` fallback for compatibility).
- Type Safety: `mypy` strict incremental + optional `pyright` + Pydantic v2 models to prevent schema drift.
- Code Style: Ruff for combined lint + format to minimize tooling overhead.

Adopt Now: Lock to Python 3.12, add CI script to run nightly 3.14 test container; capture incompatibilities early.

### 3.3 Core Backend Components (Human Readable)

- API / Service: Adopt FastAPI now (lightweight layer); prepare JSON + streaming endpoints; defer GraphQL / gRPC.
- Internal Modules: Segment under `src/backend` (ingest, enrich, stance, search, export); maintain thin contracts; defer plugin marketplace abstraction.
- Background Tasks: Start with simple `asyncio` or on‑demand CLI triggers; later introduce APScheduler if periodic tasks grow; defer heavy workflow engines.
- Caching: Use in‑process LRU + on‑disk SQLite for expensive fetch memoization; consider Redis if multi‑process arises; defer distributed tiers.
- Config: Centralize with `pydantic-settings` + `.env`; later add hierarchical profiles; defer external secrets managers.

Rationale: Separating FastAPI early decouples UI pivot risk; you can mount MCP servers alongside FastAPI in a Starlette app if needed.

### 3.4 Data Layer (PostgreSQL + pgvector) – Human Readable

- Primary DB: Local PostgreSQL 17 (stable; simple local operation).
- Vector Extension: pgvector with exact search first; only add approximate index if >~100k records slows queries.
- Tables Layout: Single `capture` schema: awards, subawards, entities, capability_tags, enrichment_logs, embeddings, relationships (keeps mental model clear).
- Changes / Migrations: Use Alembic to version schema changes and enable rollback.
- Indexes: Target agency, naics_code, end_date, tag arrays, embedding vectors for performance.
- Data Checks: Validate on load with Pydantic; send invalid rows to quarantine log.
- Speed Monitoring: Log occasional slow queries; avoid heavy monitoring until justified.

When to Consider Extra Tools: If vector search becomes noticeably slow or memory heavy, then test a purpose‑built vector store (like Qdrant) or newer pgvector features. Do this only after you measure a real slowdown.

### 3.5 AI / LLM Layer (Human Readable)

- Local Model Runner: Ollama (simple model pull/run; easy swaps of sizes).
- Summarizer Service: Small 7B local instruct model behind `/summarize` to generate concise, source‑marked paragraphs.
- Embeddings: Lightweight embedding model (MiniLM or nomic) for fast local vectorization.
- Prompt Templates: Versioned YAML/JSON templates to reproduce generations.
- Win Theme Generation: Combine stance tags, gaps, competitor signals through template → concise bullet rewrite locally.
- Safety Checks: Enforce length, mandate source refs, reject hallucinated numeric values.
- Future: Evaluate vLLM or larger quantized models only if latency/quality issues arise.

### 3.6 MCP Integration Strategy (Human Readable)

Use MCP servers as plug‑in style tool providers (reference: modelcontextprotocol python SDK).

Categories:

- Existing / Supported Tools: Web search, browser, Git, curl, generic file, GitHub – reuse directly with minimal permission prompts.
- Custom Minimal Servers: `sam_entity_lookup`, `sam_solicitation_fetch`, `federal_award_ingest`, `capability_gap_extractor` – each focused, ≤150 LOC, built with FastMCP decorators.

Design Approach (plain terms):

- Each custom server does one clear job.
- Return structured data so the app can validate it automatically.
- Decide WHEN to call a tool outside the tool itself (keeps tools predictable if re‑run).

### 3.7 UI Strategy (Streamlit-First Simplified Plan)

Goal: Ship features fast and keep cognitive load low. Stay on Streamlit until it objectively blocks progress; skip intermediate Python web UI frameworks and go straight to a full React/Next.js front end only if clear pain appears.

Current Approach: Streamlit + a thin presenter layer (pure functions returning dicts/DataFrames) that calls FastAPI (or direct Python services) for data. Streamlit files stay as “view glue,” not business logic containers.

Why Streamlit Holds (Now):

- Ultra fast iteration for single-user workflows.
- Built-in widgets cover current needs (filters, tables, basic charts, download/export buttons).
- Zero extra stack (no Node toolchain) keeps environment simpler while core data & AI layers harden.

Known Limitations (Accepted For Now):

- Coarse-grained reruns; some inefficiency tolerated.
- Limited fine-grained state; complex multi-pane editors can get clumsy.
- Custom component development slows momentum—avoid unless absolutely needed (e.g., virtualized long table).

Single Future Pivot (If Needed): Full React/Next.js + FastAPI API layer.
No interim migration (NiceGUI, Dash, Panel, etc.) to avoid churn and duplicated UI logic.

Migration Triggers (Need ≥2 “Moderate” OR 1 “Severe” – Human Readable List):

- Moderate – Layout density hurting clarity (e.g., stance editor requires awkward tab/nesting hacks).
- Moderate – State hacks proliferating (>3 distinct session_state workaround clusters on one page).
- Moderate – Performance irritation (common interaction rerender >300 ms OR full page >2 s even when cached).
- Moderate – Need richer client interactions (inline editable grid >5k rows, drag/drop planning board).
- Severe – Multi-user/auth requirement emerges (shared remote access needed).
- Severe – Strategic UI extensibility need (component theming/library impossible in Streamlit).

If a severe trigger fires OR two moderates persist for two consecutive iterations, schedule the React migration.

Near-Term UI Engineering Checklist:

1. Extract presenter functions returning plain dicts/DataFrames for each panel (search results, stance summary, enrichment status).
2. Centralize formatting (numbers, dollars, dates) in a small `ui_format.py` module.
3. Add lightweight caching (st.session_state or @st.cache_data) only where it saves >100 ms and avoids stale logic complexity.
4. Keep each Streamlit page under ~300 lines; refactor earlier if creeping above.
5. Log simple UI timing (render start/end) for stance editor and search panels to watch for drift toward trigger thresholds.

Deferred Until Migration Decision:

- Custom JavaScript components.
- Complex client-side state machines.
- Reactive graph visualizations beyond simple charts.

Outcome: Minimal effort now, low friction later—because data shaping and formatting are already separated, the React rewrite (if needed) swaps only the view layer.

### 3.8 Orchestration, Agents & Tooling (Human Readable)

- Light Agent Flows: Use LangChain now for basic tool calling & templating; later consider LangGraph if workflows become multi‑step.
- Data Integrity Layer: Pydantic models validate IO schemas; add schema diff tests in CI later.
- Conversation Memory: Ephemeral window + stance/last query context injection; vector store only if justified.
- Repeatable Pipelines: Pure functions with input hashing to skip unchanged work; add caching layer if runtimes grow.

Keep it simple: avoid adding heavy workflow tools until you actually need timed or multi‑branch flows.

### 3.9 Packaging, Dependencies & Environments (Human Readable)

- Manifest: Move to `pyproject.toml` (retain `requirements.txt` export for compatibility).
- Locking: Use `uv lock`; commit lock file.
- Dependency Hygiene: Track KEEP vs DEV; alert if KEEP > 35.
- Local Scripts: Provide CLIs (ingest, enrich, rebuild_embeddings, export_profile).
- Versioning: Semantic version tags post MVP; expose module `__version__`.
- Repro Mode: Supply `make repro` or Windows `scripts\repro.cmd` for env + smoke tests.

### 3.10 Observability & Quality (Local Only – Human Readable)

- Logging: Structured JSON to `logs/` (timestamp, level, module, event, entity_id, hash).
- Light Metrics: Periodic summaries (ingest time, enrichment success %, embedding latency); no external Prometheus yet.
- Testing: Pytest + fixtures; golden summary hash assertion tests.
- Performance Timing: Simple helper logs sample durations; watch slow enrichment tail.
- Quality Gates: CI runs lint, type, tests, integration smoke; block merges on unexplained stance diff.

### 3.11 Security / Privacy

Local single user still needs:

- Strict allowlist for outbound HTTP domains (SAM.gov, NAICS/PSC lookup, approved web snapshot). One config array.
- All external fetches logged with reason; no silent calls.
- Environment variables (.env) contain only non‑secret configuration initially; if API keys appear later, document rotation procedure.
- Embed only sanitized text (strip PII if inadvertently present). Add heuristic scanner (regex for emails, SSNs) → warn & skip.

### 3.12 Migration & Evolution Roadmap (Human Readable)

- Phase 0 (Now): Extract FastAPI layer, presenter functions, centralized formatting & config.
- Phase 1: Instrument timing, catalog session_state hacks, maintain trigger scoreboard.
- Phase 2: If ≥2 moderate or 1 severe trigger: scaffold React/Next.js (auth‑ready, stance editor first, reuse JSON contracts).
- Phase 3: If embeddings >1M or latency over target: add approximate vector index / evaluate Qdrant.
- Phase 4: Multi-user need: introduce JWT auth, roles, shared Postgres.
- Phase 5: Frequent long-running scheduling: add APScheduler; only then consider Prefect/Airflow.

### 3.13 Stack Summary (Adopt / Prepare / Defer – Human Readable)

- Runtime: Adopt Python 3.12 + uv + Ruff + mypy; prepare 3.14 test matrix; defer free‑threaded opt‑in.
- Backend: Adopt FastAPI modular services; prepare Starlette mount of MCP; defer GraphQL/gRPC.
- UI: Adopt Streamlit + presenter; prepare monitoring + JSON endpoints; defer Next.js until triggers.
- Data: Adopt Postgres 17 + pgvector exact; prepare approximate index if slow; defer dedicated vector DB.
- AI: Adopt Ollama 7B + local embeddings; prepare vLLM eval; defer fine‑tuning pipeline.
- Agents: Adopt minimal LangChain; prepare selective LangGraph; defer autonomous orchestration.
- Observability: Adopt local JSON logs + pytest; prepare metrics wrappers; defer external APM.
- Packaging: Adopt pyproject + lock; prepare release automation; defer container orchestration.
- Scheduling: Adopt manual/CLI; prepare APScheduler; defer Prefect/Airflow.
- Caching: Adopt in‑process LRU; prepare Redis if multi‑process; defer distributed cache.

### 3.14 Action Checklist (Engineering ToDos)

Plain language tasks derived from this stack (can be mirrored into a task tracker):

1. Introduce `pyproject.toml` + migrate dependencies; keep `requirements.txt` export.
2. Add FastAPI app under `src/backend/api` exposing: health, search(query), capability_stance, enrichment_trigger.
3. Wrap existing data access logic into repository layer (award_repo, subaward_repo).
4. Add Pydantic models: AwardRecord, SubawardRecord, EnrichmentLogEntry, CapabilityTag.
5. Implement simple embedding service wrapper (lazy load model; skip re‑embed if text unchanged).
6. Add summarizer endpoint `/summarize` using local Ollama model (include source id injection and safety checks).
7. Add MCP custom server stubs: `sam_entity_lookup`, `sam_solicitation_fetch` with structured outputs.
8. Create UI adapter (presenter) that returns plain dict data for each dashboard panel.
9. Add summary golden tests: given sample award set -> expect summary paragraph hash.
10. Implement outbound domain allowlist check before any HTTP call.
11. Add nightly script: run tests under Python 3.14 (when final) + log performance numbers.

### 3.15 Why This Stack Serves the Product Principles

- Local & Private: All core services local; optional external calls tightly gated.
- Capability Baseline First: Structured models and repository layer make stance a first-class queryable object.
- Modular by Default: Clear seams (ingest, enrich, stance, search, export, ui adapter, mcp tools).
- Fast Feels Better: Lean stack avoids heavy overhead; direct Python + Postgres.
- Reuse Before Build: MCP + open-source embeddings + Ollama minimize bespoke code lines.
- Plain Language: Stack decisions expressed in everyday terms; no hidden complexity.
- Extensible: Migration roadmap prevents lock-in while postponing cost until justified by signals.

---

Open Questions (To Confirm Later):

1. Do we need an offline bundle script to package model weights for no‑internet environments now or later?
2. What is the slowest acceptable similarity search time for a typical query (propose target: under 150 ms for 100k items)?
3. What is an acceptable total time for a full enrichment run (propose under 10 minutes for the current dataset size)?

These can be added once performance baselines are measured.

## 4. Data Sources & Acquisition Plan (Draft)

This section catalogs the concrete data sources (current, enrichment, planned) that feed the capability stance, competitive analysis, semantic search, and opportunity/recompete workflows. It defines: scope, acquisition method, key fields, data quality considerations, join keys, enrichment logic, refresh cadence, and readiness tier.

### 4.1 Source Classification Overview (Human Readable)

- Core / Current: Already ingested & local; drives main analytics (e.g., USAspending prime & subawards 2012‑10‑01 → 2025‑03‑31).
- Aux / Enrichment: Selective pulls to fill description, metadata, classification gaps (archived SAM.gov solicitations/PWS, SAM.gov entity lookups).
- Plan / Near-Term: High strategic value targeted soon (SAM.gov active opportunities, ad hoc Web Intelligence tool).
- Fut / Planned R&D: Deferred until core loop stable or API access justified (SBA SubNet, Mentor‑Protégé, NATO NSPA, BLS, GovWin, Bloomberg Gov, Salesforce).

### 4.2 Core Historical Contract Data (USAspending)

Current temporal coverage: 2012-10-01 (FY2013 start) through 2025-03-31.

Canonical Database Context:

- Database: `capture_insights`
- Schemas (pipeline stages): `s1_raw` (raw), `s2_interim` (cleansed), `s3_processed` (deduped + analytics)
- MVP PRD Reference Focus: For stance derivation & analysis we operate primarily from `s3_processed` standardized tables. (User note: Provided interim names `s2_interim.usaspending_prime_awards_dedbup` and `s2_interim.usapsening_subawards_enriched`—spelling/consistency to be normalized).

Primary Tables (Logical Intent – Human Readable)

- Prime Awards – `s2_interim.usaspending_prime_awards_dedbup`: Deduped prime transactions. Action: fix typo to `dedup`; replicate in `s3_processed` for stable analytics.
- Subawards – `s2_interim.usapsening_subawards_enriched`: Subaward joins + enrichment fields. Action: correct spelling, unify naming + keys, maintain referential link to prime via award/PIID.

Key Join & Identity Fields:

- `award_id_piid` (or equivalent PIID / FAIN depending on award type) – internal canonical award key.
- `contract_transaction_unique_key` (prime row-level uniqueness).
- `contract_award_unique_key` (stable prime award identifier; equals the `prime_award_unique_key` value present in subaward records and serves as the primary join key prime → subawards).
- Subawards composite identity: (`prime_award_unique_key`, `subaward_number`, `subaward_action_date`).
- Recipient entity resolution: `recipient_uei`, `recipient_name`, `recipient_parent_name`,`recipient_parent_uei`.
- Subaward recipient keys: `subawardee_uei`, `subawardee_name`.

Essential Fields for Capability & Gap Logic:

- Descriptive text fields: `prime_award_base_transaction_description`, `transaction_description`.
- Classification codes: `naics_code`, `product_or_service_code` (+ augmented descriptions).
- Financials: `federal_action_obligation`, cumulative obligated amounts, subcontract amount proxies where inferable.
- Period: `action_date`, `period_of_performance_start`, `period_of_performance_current_end`.
- Competition & set‑aside indicators: `extent_competed`, `type_of_set_aside`, `socioeconomic_indicators` (if available).

Data Quality Focus Items:

- Inconsistent description detail density—drives enrichment trigger scoring.
- NAICS / PSC misalignment or missing codes—flag for potential enrichment disclaimers.
- Subaward sparsity (reporting gaps) – store reliability tier metric (percent of expected sub award coverage?).

Immediate Schema Hygiene Tasks:

1. Normalize table names (deduped vs enriched) to remove typos.
2. Promote cleaned, deduped, analytics-ready tables into `s3_processed` with stable naming (`usaspending_prime_awards`, `usaspending_subawards`).
3. Implement view synonyms if legacy names needed for backward compatibility.

### 4.3 Enrichment via SAM.gov (Inactive / Historical Artifacts)

Purpose: Improve contract descriptive richness (PWS/SOW/solicitation paragraphs) to strengthen capability tag extraction and summarization accuracy.

Public API Reference (supplemental): https://open.gsa.gov/api/get-opportunities-public-api  
Used here strictly to assist in back-linking historical award PIIDs to archived notice metadata when available; primary focus remains extraction of textual artifacts for enrichment.

Acquisition Strategy:

1. Given an award from prime table, attempt to map to archival solicitation (PIID / notice ID heuristic mapping).
2. Fetch document metadata + textual sections (scope, objectives, performance requirements).
3. Extract paragraphs with regex + section heading heuristics.
4. Store in `sam_gov_solicitation_descriptions` (array / JSONB) per award.

Trigger Heuristic (executed during enrichment job):

- IF (description_coverage_score < threshold) AND (no prior successful solicitation fetch within 30 days) THEN attempt inactive solicitation retrieval.

Data Elements Captured:

- `solicitation_id`, `notice_type`, `published_date`, `extracted_sections[]`, `fetch_timestamp`, `source_url`.

Error / Fallback Handling:

- Network / 404: log attempt; set status = `missing_artifact`.
- Parsing failure: retain raw text blob, mark `parse_status = partial`.

### 4.4 Enrichment via SAM.gov (Active Opportunities)

Purpose: Feed forward-looking pipeline (RFI, Sources Sought, Draft RFP, Final Solicitation) for early capture posture + transition candidate detection.

Public Entity API Reference (supporting metadata & cross-validation): https://open.gsa.gov/api/entity-api  
While this API surfaces entity registration facets, within this active opportunities context it is leveraged to (a) confirm entity identifiers appearing in new notices and (b) enrich early-stage notices with basic vendor metadata when relevant to overlap scoring.

Scope Notice Types (initial subset): RFI, Sources Sought, Presolicitation, Solicitation, Award Notice (link-back validation), Justification & Approval (optional later).

Storage Plan:

- Table: `sam_active_notices` (new) with incremental fetch (since last published date).
- Join Fields: `notice_id`, potential mapping to future award: store candidate PIID reference when present.
- Derived Fields: `lifecycle_stage` (rfi | sources_sought | presolicitation | solicitation | award_linked), `candidate_transition_flag` (if overlaps expiring incumbent theme), `capability_tag_overlap_score` (computed via semantic similarity to stance tags).

Refresh Cadence: On-demand + optional daily scheduled pull (deferred scheduling automation until scheduler phase).

### 4.5 Ad Hoc Web Intelligence Tool

Purpose: Contextual enrichment for entities (primes, subs, potential partners) and niche capability emergence signals.

Inputs (seeded from DB): `award_id_piid`, `recipient_name`, `recipient_uei`, `subawardee_name`, `subawardee_uei`, optional domain guess.

Acquisition Modes:

- Targeted Web Search (restricted allowlist engines / API or local headless browser with rate guard).
- Light crawl depth = 1 (homepage + /about or /capabilities when present).
- Optional social snapshot (X.com) summarization – limited to latest N posts (N ≤ 10) to avoid drift.

Output Schema (Proposed JSONB per Entity – Human Readable)

- entity_uei (text): Entity linkage key.
- fetch_timestamp (timestamptz): Collection time.
- domains (text[]): Resolved domains visited.
- capability_snippets (text[]): Short deduped extracted sentences.
- emerging_keywords (text[]): High tf‑idf / novelty terms vs baseline.
- social_signals (text[]): Summarized recent focus posts.
- source_urls (text[]): Provenance URLs.
- coverage_score (numeric): Percent of desired fields present.

Integration With Stance Pipeline:

- After insert/update, recompute stance tag confidence adjustments where new capability_snippets raise frequency.
- Maintain change hash to skip re-embedding if no material text delta.

### 4.6 Entity & Registration Data (SAM.gov Entity Lookup)

Purpose: Add formal size status, socio-economic flags, and registration canonical name variants for entity conflation and stance context.

Captured Fields (subset): `uei`, `legal_business_name`, `duns` (if present), `sam_status`, `registration_expiration_date`, `small_business_indicator`, `socio_economic_flags[]`.

Refresh Strategy: On-demand (entity appears without cached registration or data older than 30 days) → queued lookup.

### 4.7 Planned / Deferred External Sources (Human Readable)

- SBA SubNet: Subcontracting opportunity discovery (Priority: Medium; after SAM active pipeline stabilizes).
- SBA Mentor‑Protégé Agreements: Partner relationship & teaming leverage (Medium; enriches relationship strength context).
- NATO NSPA: International opportunity awareness (Low/Medium; separate schema; optional adjacency).
- BLS API: Economic context / inflation indices for pricing narratives (Low; used only in pricing/trend sections).
- GovWin IQ: Proprietary early pipeline intelligence (Deferred; paid access; post‑MVP validation).
- Bloomberg Government: Competitor & financial intelligence (Deferred; same gating as GovWin).
- Salesforce: CRM sync (opportunity stage tracking) (Deferred; only if multi‑user/process management emerges).

### 4.8 Data Dictionary Seed (Prime & Subaward Fields – Human Readable)

Initial priority columns to formalize (subset; final dictionary adds type, source layer, flags, example values):

- award_id_piid (prime/sub): Canonical award identifier for joins & provenance.
- contract_transaction_unique_key (prime): Row-level uniqueness key for prime transactions.
- prime_award_base_transaction_description (prime): Original base transaction descriptive text.
- transaction_description (prime): Modification-level description text when distinct.
- naics_code (prime/sub): Industry code.
- product_or_service_code (prime/sub): PSC classification.
- federal_action_obligation (prime): Dollar amount obligated for transaction.
- subcontract_reliance_flag (prime): Derived indicator of high subcontract percentage.
- subaward_description (sub): Original subaward purpose text.
- subaward_amount (sub): Dollar amount of subaward action.
- subawardee_uei (sub): Subaward recipient UEI.
- subawardee_name (sub): Subaward recipient name.
- inferred_subaward_rationale (sub): Derived purpose classification.
- capability_tags_draft (prime/sub): Auto‑extracted preliminary capability tags.
- capability_tags_final (prime/sub): User‑curated final capability tags.
- summary_paragraph (prime/sub): Consolidated enriched summary.
- embedding_vector (prime/sub): Vector representation for semantic search.
- data_enrichment_status (prime/sub): Enum marking completeness (base_only / partial / enriched).

Action: Script generation of this dictionary into `docs/DATA_DICTIONARY_PRIME_SUBAWARD.md` (future task) using inspection + curated descriptions.

### 4.9 Refresh & Change Detection Strategy (Human Readable)

- Historical awards: Batch refresh when new quarterly/monthly drop ingested; idempotent transforms.
- Active notices: Incremental fetch since last timestamp; maintain high‑water mark.
- Entity lookups: On‑demand with 30‑day TTL cache.
- Web intelligence: Manual or user‑triggered enrichment with per‑entity cooldown (≈7 days).
- Embeddings: Recompute only if content change hash differs.
- Summaries: Regenerate only when any source component text changes (base, solicitation, external snippets).

### 4.10 Provenance & Audit Logging

Each enrichment or external fetch produces a log entry (table: `enrichment_logs`):

- `id`, `entity_type` (award|entity|notice|web_entity), `entity_id`, `tool_name`, `trigger_reason`, `status`, `started_at`, `finished_at`, `duration_ms`, `fields_added[]`, `error_message` (nullable), `hash_before`, `hash_after`.

Benefits: Supports diff-based reprocessing, selective rollback, and future supervised tuning dataset extraction (filter by fields_added + confidence changes).

### 4.11 Readiness & Risk Summary (Human Readable)

- USAspending Prime/Sub – Readiness: High | Risk: Description sparsity | Mitigation: Solicitation enrichment + stance evidence weighting.
- SAM Inactive (artifacts) – Readiness: Medium | Risk: Imperfect PIID↔notice mapping | Mitigation: Fuzzy matching + manual override queue.
- SAM Active Notices – Readiness: Medium (planned) | Risk: Rate limits / evolving fields | Mitigation: Throttling, schema versioning, test harness.
- Web Intelligence – Readiness: Low (initial) | Risk: Noise / hallucination | Mitigation: Snippet caps, deterministic merge order, source logging.
- Entity Lookups – Readiness: Medium | Risk: Stale registrations | Mitigation: TTL refresh + status flag.
- Deferred Sources (SBA, GovWin, etc.) – Readiness: Planned/Deferred | Risk: Access/licensing/scope creep | Mitigation: Gate behind explicit ROI trigger.

### 4.12 Immediate Next Actions (Data Source Track)

1. Normalize prime/sub table names; promote to `s3_processed` canonical names.
2. Implement solicitation enrichment storage (`sam_gov_solicitation_descriptions`).
3. Define `sam_active_notices` schema + high-water mark fetch logic (scaffold only; population later).
4. Create `enrichment_logs` table + logging wrapper.
5. Generate automated data dictionary skeleton (prime/sub) to Markdown.
6. Implement description coverage & enrichment trigger scoring function.
7. Add web intelligence MCP tool stub (returns capability_snippets + emerging_keywords).

This completes foundational Section 4; later iterations can append deeper schema diagrams or API field mapping appendices.

## 5. Features & User Experience (Draft)

Plain language description of what the user (single capture analyst) can do, how each screen/panel behaves, what “done” looks like, and success criteria to test against. This section converts earlier data + architecture foundations into concrete user-facing value.

### 5.1 Persona & Context (Human Readable)

Persona: Solo Capture Analyst (You)

- Description: Combines analyst + strategy roles; must explore, size, qualify, and draft quickly.
- Constraints / Assumptions: Single local machine; limited time; every claim must be traceable.
- Primary Pain Points (expanded):
  - Tool / tab sprawl (spreadsheets, browser tabs, SAM searches, ad‑hoc notes without linkage).
  - Slow recompete identification and manual narrative drafting.
  - Inconsistent capability list reuse across pursuits.
  - Fragmented information (PDFs, emails, portals, CSV dumps) without a central context hub.
  - Manual data mining (copy/paste, keyword search) with little automation or local LLM leverage.
  - Missing semantic search spanning enriched awards, subawards, and external snippets.

### 5.2 Jobs To Be Done (Human Readable)

- Market Overview – Show slice shape (agency + NAICS/PSC + time) → get topline spend, trend, top players(target: <10s after filters).
- Identify Recompete Window – Find sizable contracts ending soon → sorted list with end dates, value, incumbent (target: <5s list).
- Assess Incumbent Positioning – Compare incumbent vs capability stance → side‑by‑side coverage, gaps, subcontract reliance (target: <8s).
  -- Partner & Transition Discovery – Surface strategic partners and transition candidates using relationship strength, dependency flags, and capability overlap gaps (target: <8s after slice load).
- Generate Capture Profile – Produce cohesive narrative & data sections → Markdown with sources & win themes (target: ≤2 min end‑to‑end).
- Fill Description Gaps – Enrich thin award text → summary enriched without hallucination (tool call <30s, visible status).
- Semantic Find – Natural language similarity search → ranked relevant awards + explanation (target: <3s query round trip).
- Prioritize Target Agencies & Prospects – Use Capture Intensity (combined award action + obligation percentiles) and Action:Obligation balance to surface high-value, active agencies and specific expiring awards or emerging requirement clusters (target: ranked list <6s).

### 5.3 Feature Inventory (Human Readable)

Core Panels & Components:

- Filter Bar or integrated on page (Slice Selector): Narrow by agency, NAICS/PSC, FY range. Inputs: user selections. Data: awards (agency, naics_code, action_date). Criteria: panels update <5s; selections persist across navigation.
- Market Overview (Metric Cards Block): Seven cards – Total Obligations, Total Award Actions, Average Award Value, Active Contracts, Expiring Contracts (6–24m window), Suitability %, Synergy %. Inputs: optimized summary query + expiring contract set + (later) capability overlap calculation. Criteria: all cards render <2s cached; values reconcile with underlying SQL sample; each card has help text.

- Trends & Projection: Quarterly obligations + award actions trend; 5-year projection model (using suitability % feed). Inputs: quarterly trends view, projection function. Criteria: trend draws <2s; projection appears if min data threshold met else shows fallback note.

- Capture Intensity Scatter: Agencies plotted by log-normalized award count vs obligations with bubble size = (capped avg award value). Criteria: scatter renders <2.5s; intensity score (0–100) = mean(percentiles of normalized count & obligation) computed client-side; tooltip shows raw + normalized; median lines visible.

- Agencies Above the Line Table: Agencies above both medians sorted by Intensity descending with formatted obligations & avg award value. Criteria: table populates <1s after scatter compute; intensity integer 0–100.

- Follow the Action Sankey: Company/Competitor → Agency → Contract (or cluster) flow to show concentration of dollars and action density (“who flows where”). Other flows may be developed beyond the example Company/Competitor → Agency → Contract (or cluster) flow. Inputs: treemap path data. Criteria: initial render <6s; node cap & aggregation applied; tooltip shows path + share.

- Recompete Radar: Contracts ending 6–24 months out sorted by value & strategic fit flag. Inputs: end dates, contract_award_unique_key. Data: period_of_performance_end, obligations. Criteria: accurate ordering; flags only when overlap > threshold; exportable.

- Incumbent Comparison: Side‑by‑side coverage %, subcontract reliance, differentiators. Inputs: capability_tags_final, subcontract ratios. Data: awards, subawards, capability tags. Criteria: coverage math correct; differentiators limited to self‑perform advantages.

- Capability Stance Editor: Approve/merge draft tags; assign classes. Inputs: capability_tags_draft. Data: capability_tags table. Criteria: deterministic merge; audit log entry; page <300 LOC.

- Lead Generator (Prospect & Partner Engine): Unified module ranking (a) target agency/requirement prospects (based on Intensity, Action:Obligation balance, expiring contracts, suitability %) and (b) teaming/transition partner candidates (relationship strength, dependency flags). Outputs two ranked lists with distinct badges (Prospect vs Partner). Criteria: stable ranking for unchanged inputs; each row displays score decomposition tooltip.

- Semantic Search: Natural language → similar awards/subawards with why snippet. Inputs: query embedding. Data: embeddings + summaries. Criteria: P@5 > keyword baseline; <3s for ≤100k vectors.

- Enrichment Status Panel: Counts of base_only/partial/enriched + retry. Inputs: enrichment logs, statuses. Data: enrichment_logs, awards/subawards. Criteria: retry logs tool entry; status refresh timely.

- Win Theme Generator: Bullets linking gaps & differentiators. Inputs: stance vs incumbent diff, tag confidence. Data: capability_tags_final, summaries. Criteria: ≥70% accept with ≤20% edits.

- Capture Profile Export: Markdown with metadata, slice summary, incumbent compare, win themes, sources. Inputs: current panel data. Criteria: file <10s; includes version, timestamp, model; passes schema lint.

- Local Operation Indicator: Badge confirms no unauthorized outbound calls. Inputs: outbound call monitor. Data: allowlist + log events. Criteria: green when only allowlist; amber on first blocked attempt.

- Flow Explorer (Money Flow Sankey): Visual flow across chosen paths (company hierarchy, prime→sub, classification). Inputs: filtered aggregates. Data: awards obligations, subaward amounts. Criteria: initial mode <6s; mode switch <2s cached; clear labels/tooltips.

### 5.4 Core Workflows (Step-by-Step)

#### 5.4.1 Market Exploration → Target Selection

1. Open dashboard (auto-restores last filter slice + last stance version hash). Background prefetch kicks off for: metric cards query, capture intensity aggregates, expiring contract window, and top N flow nodes (Sankey) using async threads/futures.
2. Adjust / refine filters (agency, NAICS, PSC, FY range, optional competitor / recipient). UI immediately reflects “Filters changed” banner for panels still recomputing; previously cached panels show stale badge until refresh completes (<5s target uncached, <2s warm).
3. Scan Metric Cards Block (Obligations, Actions, Avg Award, Active, Expiring, Suitability %, Synergy %) for anomalies (e.g., high Actions but low Obligations → fragmentation; low Synergy → poor overlap). Hover tooltips show formula + last refresh timestamp.
4. Open Capture Intensity Scatter (lazy-render after metric cards ready). Identify agencies in top-right quadrant (high normalized actions & obligations). Click one bubble → contextual mini-drawer summarizing: recent CAGR, Suitability %, Synergy %, top incumbent, top 3 differentiator tag matches.
5. Toggle “Above the Line” table view to shortlist target agencies (sorted by Intensity). Multi-select 1–3 agencies and add to provisional Target Basket (session-scoped list) with one click.
6. Launch “Follow the Action” Sankey (Company/Competitor → Agency → Contract). Validate flow concentration: look for heavy tail (large share dominated by few contracts) vs distributed spend; identify large expiring contract nodes flagged with subtle outline. (Prototype uses treemap path intermediate; final design may aggregate by contract clusters.)
7. Click a high-value contract node or row in Expiring Contracts card drill-down → side drawer: incumbent summary (obligations to date, months to end, subcontract reliance %, top stance gaps, last enrichment date).
8. (Optional) Open Recompete Radar full view for 6–24 month window; apply secondary filters (min obligation threshold, incumbent reliance > X%). Sort descending by strategic flag (derived from capability overlap + differentiator gaps).
9. From drawer or radar row, click “Compare to My Stance” → incumbent comparison panel renders with coverage %, differentiators, gap candidates (instant read since stance preloaded); suitability & synergy recalculated for selected contract if not cached (<1.5s target).
10. Decide action: (a) Add Contract to Profile Draft, (b) Mark Watch (stores in lightweight watchlist table), or (c) Dismiss (suppresses for current session unless filters change substantially). UI logs selection event locally.
11. Repeat steps 4–10 until Target Basket contains ≥1 agency and 2–5 candidate contracts OR user reaches diminishing returns (no new high Intensity / Synergy gains).
12. Proceed to Capability Refinement Loop (if new gaps emerged) or directly to Lead Generation (Partner & Transition Discovery) with basket context passed forward.

Prototype Improvement Brainstorm (market_overview.py is a reference, not a constraint)
The current prototype logic (single synchronous query + sequential chart building) can be evolved along these dimensions:

- Async Panel Prefetch: Fire metric cards, intensity aggregates, expiring scan concurrently; resolve promises as they complete to reduce perceived latency. Success: median time to first useful panel <2.2s.
- Incremental Card Hydration: Render skeleton cards immediately; populate each card individually as data arrives (no whole-block gating). Success: Time-to-first-card vs time-to-all-cards difference logged; user perceives progress.
- Adaptive Sampling for Scatter: For very large slices, compute approximate percentiles using reservoir or t-digest then refine for top quadrant on demand. Success: Scatter initial render stays <2.5s at 5x data volume.
- Opportunity Heuristics Inline Badges: Add micro-badges beside agencies: “Momentum” (if CAGR > threshold), “Fragmented” (high actions:obligation imbalance), “High Fit” (Suitability > threshold). Success: Reduces clicks to discover key attributes (baseline vs instrumented session A/B later).
- Target Basket Persistence: Store basket in local lightweight table with stance version hash so returning to app resumes workflow. Success: ≥90% basket restore accuracy after restart.
- Flow → Radar Handshake: Selecting a contract cluster segment in Sankey auto-filters Recompete Radar to those contract IDs. Success: 1-click path-to-detail; reduces manual searching.
- Inline Lead Pre-Score: Display faint composite prospect score (from 5.10 logic) next to agency rows before user navigates to full Lead Generator. Success: Correlation >0.9 between inline and final scores; fewer context switches.
- Formula Explain Mode: Toggle overlays formulas directly on cards (in-place) instead of separate help tooltips; auto-hides after inactivity. Success: Lower help-click repetition rate.
- Keyboard Shortcuts: e.g., (R) open Recompete Radar, (F) Focus filters, (L) Toggle flow explorer, (B) Add current selection to Basket. Success: Power user flow time reduction (tracked via logged action intervals).
- Data Freshness Strip: Subtle bar showing last update timestamps for prime, subaward, enrichment, stance snapshot; turns amber if any exceeds freshness SLA. Success: Proactive user awareness; fewer manual “is this current?” checks.
- Graceful Degradation: If vector similarity needed for Suitability % not ready, card shows placeholder + queued icon instead of delaying whole panel. Success: Zero full-panel blockers from single missing component.
- Extensible Sankey Modes: Architect builder to accept generic node level config so later we can add NAICS → Agency → Prime → Sub flows without rewriting aggregation logic. Success: Adding a new 3–4 level mode <1 dev day.
- Pre-Decision Summary Panel: Once Basket has contents, show consolidated statistics (combined obligations, average months to expiration, aggregate suitability) as a sticky footer prompting next step (Refine Stance or Generate Profile). Success: Increases conversion to profile generation sooner.
- Observability Hooks: Log timings per panel + data volume snapshot to refine thresholds; export anonymized timing summary locally for tuning. Success: Ability to detect regressions pre-user frustration.

Implementation Notes (forward-looking):

- Presenter Layer should expose discrete async-friendly coroutines (get_metric_cards, get_intensity_data, get_expiring_contracts, get_flow_preview) returning lightweight DTOs.
- Cache keys incorporate (filters_hash, stance_version_hash, dependency_version_tokens) to ensure invalidation when stance or enrichment changes invalidate derived metrics (e.g., Suitability %, Synergy %).
- Suitability % fallback: if required overlap embeddings missing, compute quick heuristic using NAICS/PSC intersection ratio; mark card with fallback badge.
- Synergy % (working concept): portion of obligations in slice aligned to differentiator tags; keep computation incremental (track differentiator-associated obligations in pre-aggregated materialized view).
- Action:Obligation early warning: compute z-score of actions vs obligations; if > threshold show “fragmented micro-awards” hint encouraging filter refinement.
- Error Containment: Individual panel errors render inline compact error state; rest of dashboard remains interactive.

#### 5.4.2 Capability Refinement Loop

1. Open Capability Stance Editor (auto-loads latest approved stance + freshly extracted draft tags from historical prime/sub award corpus and any new enrichment artifacts).
2. System auto-sorts draft tags (confidence ↓, then recency) and surfaces suggested merge groups (e.g., "facility ops" + "facility operations") plus provisional class hints (core / differentiator / emerging) derived from frequency, diversity, and subcontract reliance indicators (logic in capability_stance pipeline).
3. Perform light curation: one-click accept merges, optionally rename consolidated tag, adjust any incorrect class, discard obvious noise / overly generic terms (very few edits in steady state).
4. (Optional) Inspect evidence snippets for low-confidence or emerging tags; keep only if at least one clear award / enrichment sentence supports it; otherwise delete.
5. Commit (manual click or auto-commit after inactivity timeout) → new snapshot & version hash persisted; Incumbent Comparison, Lead Generator, Win Theme Generator re-read stance immediately.
6. Done. Typical cycle <2 minutes unless major data ingest just occurred; manual free-form tag addition is rare and requires rationale note (preserves evidence-first integrity).

Guiding Note: Refinement is intentionally minimal—historical contract text + enrichment already generate a high-quality draft set; the user acts as a light-weight curator, not a primary authoring source.

#### 5.4.3 Lead Generation (Partner & Transition Discovery)

1. Navigate to Lead Generator tab.
2. System pre-loads relationship metrics for current slice (cached computation if unchanged).
3. Transition candidates flagged (theme where you sub historically + self-perform elsewhere + upcoming recompete).
4. Click a partner row → rationale panel (strength score breakdown + shared themes + suggested next action).
5. Option: “Add to Capture Profile Draft” toggles inclusion.

#### 5.4.4 Enrichment & Gap Filling

1. From any sparse award (badge: “Thin Description”), click “Enrich”.
2. Tool queue entry created; status moves from pending → running → enriched/failed.
3. On completion, summary + tags refresh; change hash triggers re-embedding.

#### 5.4.5 Capture Profile Assembly & Export

1. Click “Generate Profile”.
2. Dialog: choose which selected opportunities (checkbox), include win themes (yes/no), include partner rationale (yes/no).
3. System composes Markdown: header (filters + timestamp + model), market slice section, incumbent comparison, capability stance snapshot, win themes, partner list, selected opportunities details, sources.
4. File saved to /exports (configurable) and downloadable via Streamlit button.

### 5.5 Panels / Screens (Layout & Data Contract – Human Readable)

- Filter Bar: Components – agency multi‑select, NAICS/PSC multiselect, FY range slider, reset. Returns: agencies[], naics_codes[], psc_codes[], fy_range. Notes: state persists via session_state.
- Market Summary: Components – KPIs (Total Obligations, YoY %), mini timeline, top contractors & codes. Returns: obligations_total, obligations_yoy_pct, timeline[{fy, obligation}], top_contractors[{entity_uei,name,obligation,share_pct}], top_codes[]. Notes: hover reveals raw numbers + calc formula.
- Recompete Radar: Components – table with sort & months filter. Returns rows[{contract_award_unique_key, incumbent_name, end_date, total_obligation, months_to_end, capability_overlap_pct, strategic_flag}]. Notes: row click opens side drawer.
- Incumbent Comparison: Components – coverage bars, differentiators list, subcontract reliance chart. Returns incumbent_tags[], my_tags[], differentiators[], gap_candidates[]. Notes: bar colors (green self‑perform adv, amber gap, gray parity).
- Capability Stance Editor: Components – draft tag list, merge controls, classification dropdown. Returns draft_tags[], final_tags[], merge_actions[]. Notes: inline validation avoids duplicate final names.
  -- Lead Generator: Components – dual tabs (Prospects, Partners). Prospects: high-intensity agencies + expiring contracts scored by Intensity, Action:Obligation balance, suitability %, proximity to expiration. Partners: ranked relationship edges (strength_score, dependency_flag, transition_candidate). Returns prospects[{agency_or_contract_id, intensity_score, action_obligation_ratio, suitability_pct, expiration_risk, composite_lead_score}], partners[{entity_uei,name,strength_score,shared_themes_count,dependency_flag,transition_candidate_flag}]. Notes: each row tooltip shows score breakdown; selection adds to export set.
- Semantic Search: Components – query box, results list, snippet. Returns results[{id,type,score,why_snippet,source_tags[]}]. Notes: snippet highlights matched terms/phrases.
- Enrichment Status: Components – counts, table, retry buttons. Returns summary_counts{base_only,partial,enriched}, rows[{entity_type,id,status,last_attempt,fail_reason?}]. Notes: retry triggers async call with optimistic UI.
- Win Theme Generator: Components – bullets + sources. Returns themes[{bullet, source_ids[], rationale_type}]. Notes: user can exclude bullet pre‑export.
- Profile Export Dialog: Components – option checkboxes, preview area. Returns options{include_themes,bool; include_partners,bool; selected_opportunity_ids[]}, preview_summary. Notes: shows estimated token size & filename.
- Flow Explorer: Components – Sankey diagram, mode selector, top N slider, hover highlight, click drill. Returns flow_mode, nodes[], links[], meta{mode,filter_slice,aggregation_notice}. Notes: node limit per level; hover shows dollars + %; contract click opens detail drawer.

### 5.6 States & Feedback (Design Guidance – Human Readable)

- Loading (short <1s): Market Summary, Recompete Radar – show skeleton placeholders (no spinner) → light gray bars/rows.
- Loading (long ≥1s): Enrichment run, large semantic search – show spinner + “Processing locally…” message → spinner with subtle pulse.
- Empty: Recompete Radar (no contracts) – show friendly message + link to adjust filters → info icon.
- Partial: Award detail drawer (some fields enriched) – badge “Partially Enriched – click to complete” → amber badge.
- Error: Enrichment Status (tool failure) – row displays fail_reason + retry button → red outlined row.
- Stale: Any cached panel after filter change – yellow banner “Filters changed – refresh panel”.
- Local OK: Global indicator green shield “Local only”.
- Blocked Outbound: Global indicator amber shield “Blocked request to domain X”.

### 5.7 Performance & Quality Targets (Initial – Human Readable)

- Filter → Market Summary render: <5s uncached, <2s cached (maintains flow) – measure with timer logs median/p95.
- Semantic search round trip (≤100k vectors): <3s (preserves exploratory feel) – benchmark fixed queries.
- Recompete Radar load: <5s (sorting + filtering should not block) – log duration.
- Win theme generation: <30s (avoid context switching) – per request timing.
- Enrichment tool call: <30s SAM, <20s web snippet (avoid long blocking waits) – log duration & success rate.
- Profile export generation: <10s (fast iteration) – time function wrapper.
- Tag acceptance rate (iteration 3): ≥70% minimal edits (LLM quality bar) – manual review sample.
- Flow Explorer initial render: <6s (top 10 per level) – timer logs p95.
- Flow Explorer mode toggle (cached): <2s (encourage comparisons) – timer wrapper.

### 5.8 Acceptance Criteria Details (Expanded – Human Readable)

- Filter Bar: 1) Filter changes update dependent panels within target time; 2) Reset returns to default FY + no agency; 3) Selections persist across tabs.
- Market Summary: 1) Totals match SQL validation (±0); 2) YoY % correct; 3) Top lists ordered correctly by share.
- Market Overview Metrics: 1) Each metric card value matches underlying query (±0); 2) All seven cards render <2s cached / <4s cold; 3) Help text present; 4) Suitability & Synergy show placeholder badge if model inputs incomplete.
- Recompete Radar: 1) Only 6–24 month window contracts; 2) Strategic flag only when overlap ≥ threshold; 3) Sorting works both directions on months_to_end.
- Incumbent Comparison: 1) Coverage % formula correct; 2) Reliance bars reflect computed buckets; 3) Differentiators exclude strongly self‑performed incumbent tags.
- Capability Stance Editor: 1) Merge produces single approved tag & removes originals; 2) Class change instantly updates counts; 3) Versioning stores hash + timestamp.
- Lead Generator: 1) Prospect composite score deterministic given same inputs; 2) Score tooltip decomposes weights; 3) Action:Obligation ratio displayed (rounded) for each prospect; 4) Partner list still exposes strength_score + dependency flag; 5) Transition candidate flag only when criteria met; 6) Row click reveals rationale <1s.
- Semantic Search: 1) Seeded queries return at least one result; 2) Why snippet has overlapping term/variant; 3) Stable results with unchanged embeddings.
- Enrichment Status Panel: 1) Retry logs new entry; 2) Status transitions recorded; 3) Failed row shows retry option.
- Win Theme Generator: 1) Each bullet has ≥1 source id; 2) No new numeric values appear; 3) User can exclude bullet pre‑export.
- Capture Profile Export: 1) Header metadata present; 2) Sections ordered per spec; 3) Source links resolve to existing ids.
- Local Operation Indicator: 1) Green by default; 2) Amber on off‑allowlist attempt; 3) Click opens outbound call log.
- Flow Explorer: 1) Initial mode respects top N per level, no empty labels; 2) Outgoing shares sum ~100% (rounding tolerance); 3) Mode switch preserves filters; 4) Hover tooltip shows cumulative path share; 5) Contract node click opens detail <1s.

### 5.9 Capture Profile (Markdown) Structure (Draft Spec)

Order & Required Sections (each section preceded by H2 / H3 headings):

1. Title Block: Profile Title, Generated Timestamp, Filter Slice (Agencies, NAICS/PSC, FY Range), Model Name, Stance Version Hash.
2. Market Overview: Totals, YoY change, top contractors, top NAICS/PSC codes.
3. Target Opportunities (Recompete Radar subset): Table with: Contract ID, Incumbent, End Date, Obligation, Capability Overlap %, Strategic Flag.
4. Incumbent Comparison (per selected target): Coverage summary, differentiators, gap list.
5. Capability Stance Snapshot: Core / Differentiator / Emerging tags (comma or bullet), any new emerging tags flagged.
6. Win Themes: Bulleted, each with source ids list in parentheses.
7. Partner & Transition Candidates: Table or bullet list (partner, strength score, rationale highlights).
8. Methodology & Source Notes: Short explanation (data period, enrichment notes, limitations badges if any).
9. Appendices (Optional): Raw filter SQL (or description), tag version diff, enrichment log summary counts.

Formatting Rules:

- Monetary values: $X.XXM (≥1,000,000) else $X,XXX.
- Dates: YYYY-MM-DD.
- Percentages: whole % (rounded) unless <1%; then one decimal.
- Source Citation: [S:award_id_piid] or [S:subawardee_uei]; multi-sources comma separated.

### 5.10 Lead Scoring Logic (Initial Draft)

Purpose: Provide transparent, reproducible prioritization of which agencies / expiring contracts (Prospects tab) to engage first, distinct from partner / teaming analysis.

Scoring Dimensions (Prospects):

1. Intensity Score (0–100): Mean of percentile ranks of log-normalized award_count and obligation (from Capture Intensity scatter). Weight default: 0.30.
2. Action:Obligation Balance (A:O Ratio): (award_count_normalized / obligation_normalized). Penalize extreme imbalance (very high actions but low dollars) via sigmoid dampening. Transformed to 0–100 “Balance Score.” Weight: 0.15.
3. Expiration Proximity: For each associated expiring contract (6–24m), compute proximity score = 1 - ((days_to_expiration - min_window_days)/(max_window_days - min_window_days)). Take max. Weight: 0.20.
4. Suitability %: Percent of expiring contracts with strong capability overlap (stance vs contract description). Weight: 0.20.
5. Growth / Momentum (optional when trend data sufficient): Recent 4-quarter CAGR of obligations (clamped). Weight: 0.10.
6. Strategic Fit Modifier (optional flag): +5 bonus if differentiator tag appears in >X% of expiring contract descriptions while incumbent relies on subcontracting for that tag.

Composite Formula (normalized to 0–100):
lead_score = 100 * (0.30*Intensity + 0.15*Balance + 0.20*Expiration + 0.20*Suitability + 0.10*Momentum + bonus_modifier)
Where bonus_modifier expressed as fraction of 100 (e.g., 0.05 for +5). All component inputs scaled 0–1 before weighting.

Action:Obligation Balance Handling:

- Raw ratio r = award_count_normalized / max(obligation_normalized, ε)
- Balance Score = 100 \* (1 - |log(r)| / log(r_cap)) clipped at 0 where r_cap is a tunable symmetry threshold (default 3). This rewards near-parity between action and obligation growth signals.

Outputs & UX:

- Each prospect row shows: Intensity, A:O ratio (raw & balanced icon), Suitability %, Expiration proximity (soon / mid / later badge), Composite score.
- Tooltip: break out weighted contributions and raw values.
- Sorting: default by composite; secondary interactive sort by expiration or suitability.

Acceptance Additions (Lead Scoring):

1. Recomputing with unchanged source data yields identical scores (hash of sorted (id, score) stable).
2. Turning off a weight (set to 0) re-normalizes remaining weights proportionally (UI control optional future).
3. Bonus modifier only applied if all qualifying conditions met (differentiator + incumbent reliance gap evidence present).
4. Balance Score hides (placeholder “—”) if either normalized component zero (insufficient data) and excludes from composite (weights re-normalize).
5. Audit endpoint returns JSON per prospect with component values + final score for transparency.

### 5.10 Content Safety & Integrity Rules (User-Facing Simplified)

1. No new dollar numbers invented—only reused from underlying data.
2. Every win theme bullet must list at least one source id.
3. If a section relies on partially enriched data, insert note: “Some descriptions pending enrichment – flagged with amber badges.”
4. If subcontract data reliability tier below threshold, add note in methodology.

### 5.11 Future Enhancements / Deferred UX (Markers Only – Human Readable)

List of deferred ideas with implementation triggers:

- Interactive Timeline Compare – drag select period & compare contractor shares. Trigger: user asks for dynamic trend slicing AND performance remains within targets.
- Multi-Scenario Win Theme Bundles – save alternate win theme sets (aggressive vs conservative). Trigger: >3 profile regenerations per session.
- Tag Confidence Visual Encoding – opacity or dot size to show confidence. Trigger: user confusion about certainty level emerges.
- React Migration with Rich Grid – virtualized 50k row explorer. Trigger: both migration preconditions hold for 2 consecutive iterations.
- Inline LLM “Explain This Metric” – natural language breakdown of formula. Trigger: frequent clicks on formula help tooltips.
- Profile Diff Viewer – compare two exported profile versions. Trigger: >5 saved versions for a single opportunity.

### 5.12 Open UX Questions (To Resolve Later)

1. Should Market Summary include set-aside distribution in MVP or Stage 2? (Value vs screen space.)
2. Is a mini onboarding overlay needed the first time stance editor opens? (Depends on early friction.)
3. Do we show absolute obligations and shares together or toggle? (Risk of clutter.)
4. How to represent confidence visually without overwhelming (color vs subtle icon)?
5. Minimum transition candidate criteria thresholds (tune after first dataset run).

### 5.13 Flow Explorer (Money Flow Sankey) – Detailed Spec

Purpose: Give a fast, visual answer to “Where does the money actually flow in this slice?” and “What paths (classification → agency → primes → subs) surface the biggest or most strategic opportunities?”

MVP Modes (Radio Selector):

1. Company Hierarchy Flow (Default): Parent Company → Subsidiary (if different) → Funding Sub-Agency → Top Contracts (transaction_description cluster or contract_award_unique_key label).
2. Prime → Subaward Flow: Funding Agency (or Sub-Agency) → Prime (recipient_name) → Subawardee (subawardee_name) (aggregated by total subaward_amount).
3. Classification Flow: NAICS (or PSC) → Funding Sub-Agency → Prime (recipient_name) → Subawardee (optional branch if data dense). (If subaward layer too noisy, hide when node count exceeds threshold.)

Stretch (Deferred / Hidden Toggle Until Data Validated): Expiring Contract Path: Funding Sub-Agency → Expiring Contract (within 6–24 month window) → Incumbent Prime → Your Differentiator Tag (if coverage gap exists). Only enable once expiring contract logic stable.

Data Preparation Steps:

1. Apply global filters (agency, NAICS/PSC, FY range).
2. Aggregate obligations per level pair (e.g., parent→subsidiary; subsidiary→sub_agency; sub_agency→contract) using SUM federal_action_obligation.
3. For Prime→Sub mode, aggregate subaward_amount; if missing, fallback proportion using federal_action_obligation \* (subaward_amount / total_subaward_amount for award).
4. For Classification mode, map award rows to chosen classification (NAICS or PSC) then aggregate flows along chain.
5. Rank nodes within each level by total outgoing obligation; keep top N (default 10, adjustable slider 5–25). Collapse remainder into a single “Other” node per level (if remainder share ≥5%).
6. Compute share_pct for each link relative to source node total.
7. Precompute cumulative path share (for hover display) for top K contract-level nodes (K ≤ 50).
8. Cache per-mode aggregated DataFrame keyed by (filters_hash, mode, topN) to accelerate toggles.

Node Types & Levels (Examples – Human Readable):

- Company Hierarchy: Level1 Parent Company → Level2 Subsidiary → Level3 Funding Sub‑Agency → Level4 Contract (cluster or id).
- Prime→Sub: Level1 Funding Sub‑Agency → Level2 Prime → Level3 Subawardee → Level4 (optional capability theme).
- Classification: Level1 NAICS (or PSC) → Level2 Funding Sub‑Agency → Level3 Prime → Level4 Subawardee (optional when not too noisy).

User Interactions:

- Hover: Show Source → Target, $ value, share %, cumulative path share.
- Click Contract Node: Open side drawer with: contract_award_unique_key, incumbent, end date, total obligation, top 3 capability tags, link to “Compare to My Stance”.
- Click Company / Prime Node: Side drawer: obligations total (slice), share %, top NAICS/PSC codes, subcontract ratio, link “View as Incumbent”.
- Mode Switch: Radio; retains current filters; uses cached aggregated dataset if available.
- Top N Slider: Re-aggregates (or recalls cached) with new limit; updates “Other” node share.
- Export Path Button (future): Add selected path (list of node labels + total $ + share) into capture profile draft appendix.

Visual / UX Rules:

1. Distinct color palette by level (reuse existing theme mapping).
2. “Other” node always last in that level’s vertical ordering, muted color.
3. Prevent label overlap: truncate >40 chars with ellipsis; full label on hover.
4. Minimum link display threshold: hide links with <1% of source total unless selected or hovered (improves readability).
5. Show small legend: Level colors + explanation of share basis (“Link width = % of source node total obligations”).

Performance Safeguards:

- Hard cap: Max nodes rendered ≤ 80 (sum across all levels) to avoid sluggishness.
- If potential >80 before compression, auto-enable “Aggressive Aggregation” notice (display small banner).
- Pre-aggregation SQL pushes grouping to database; Python only formats result.
- Warm cache after first build (store JSON serialized node/link structures in session_state).

Acceptance (Supplemental):

1. Sum of link values out of a node equals node total (± rounding tolerance <0.5%).
2. “Other” node share displayed if created; excluded from differentiation logic (no hover path drill into its children).
3. Cumulative path share = product of intermediate shares (verified by spot check script).
4. Mode switch does not re-run base award query (uses cached filtered DF hash).
5. Prime→Sub mode displays subaward amount; if missing >50% of subaward rows in slice, show reliability badge.

Data Model / Code Reuse:

- Reuse existing `TreemapPathElement` / `SankeyFlowElement` concepts; add lightweight adapter that builds generic FlowNode / FlowLink structures consumed by Plotly builder.
- Consider small utility: build_flow(nodes: List[dict]) -> (nodes, links, stats) with deterministic ordering for stable color assignment.
- Extend `distribution_charts.py` with `plot_sankey_flow_explorer` (wraps existing sankey function; accepts config: mode, top_n, hide_minor=True).
- Add tests: (a) aggregation correctness, (b) node count limit logic, (c) share sums.

Risks & Mitigations (Human Readable):

- Too many nodes clutter → Impact: hard to read → Mitigation: Top N + “Other” aggregation + hide minor links.
- Missing subaward data distorts Prime→Sub → Impact: misleading flow → Mitigation: reliability badge + tooltip disclaimer.
- Long labels overflow → Impact: visual clutter → Mitigation: truncate + full hover label.
- Performance slow on large slices → Impact: breaks flow → Mitigation: push aggregation to SQL + caching + node cap.
- Ambiguous parent/subsidiary mapping → Impact: incorrect hierarchy → Mitigation: fallback to prime‑only path if parent=child for >80% rows.

Future Enhancements (tie-in to 5.11): dynamic path drill-down (click expands hidden children), capability theme layer insertion between prime and contract in advanced mode, flow delta comparison (this FY vs prior FY) with dual-colored links.

Open Question Additions: 6. Do we add a PSC + NAICS merged classification layer or let user toggle separately?  
7. Threshold for hiding minor links (<1% vs user adjustable?).  
8. Is contract-level clustering (group by keyword pattern) preferable to individual contract nodes for dense slices?

### 5.14 Capability Stance Page – Detailed Spec

Purpose
: Provide a single, authoritative workspace for building, validating, classifying, versioning, and reusing the company capability stance derived from historical prime awards, subawards (issued & received), enrichment text, and external artifacts. It is BOTH: (1) a quantitative metrics snapshot (coverage, diversity, subcontract reliance context) and (2) a semi‑structured curation surface (draft → approved tags with classification). This page feeds: win theme generation, incumbent comparison panels, export profile, semantic search biasing, and teaming / transition candidate logic.

Page Objectives (User Jobs)

1. See at a glance “what we really do” based on evidence, not recollection.
2. Validate or merge auto‑extracted draft capability tags into a clean approved list (core / differentiator / emerging).
3. Understand breadth & concentration (NAICS, PSC, agency diversity, subcontract reliance signals) to inform positioning.
4. Identify internal gaps (themes mostly subcontracted) and potential transition candidates (themes where we sub for others but also self‑perform related work).
5. Generate (later) an AI narrative summary that is auditable (source-linked lines) and safe (no hallucinated numbers).
6. Chat (later) in natural language about capability coverage (“Where have we delivered defensive cyber with low subcontract reliance?”).

Primary Audience: Capture Manager (solo user) preparing a capture profile or refining internal positioning.

Scope Boundaries (MVP)

- Edit operations limited to: merge draft tags, approve/rename tag, assign class (core/differentiator/emerging), delete draft tag.
- No free‑form creation of new tags unless derived pipeline run just produced none for a major area (later enhancement). For now, allow manual “Add Tag” with mandatory evidence note (text) to preserve integrity.
- No multi‑user concurrent edits; versioning is linear with timestamp + hash.

High-Level Layout (Top → Bottom)

1. Filter Bar (shared global filters honored: date range, agency, NAICS, PSC, recent 60‑month toggle). Shows active slice pill set.
2. Metrics Strip (cards) – fetched via `get_company_performance_metrics` (to be refactored into a presenter/service):
   - Prime Awards (count), Prime Obligation ($), Subawards Received (count/$), Subawards Issued (count/$), Unique NAICS (Prime), Unique PSC (Prime), Unique NAICS (Issued), Unique PSC (Issued).
3. Coverage & Diversity Panel:
   - Top NAICS by award count (bar), Top NAICS by obligation (bar), Unique NAICS/PSC combination table (prime), Unique NAICS/PSC combination table (issued) – pagination if >200 rows.
4. Partner & Dependency Panel:
   - Top Agencies (prime), Top Prime Companies (when we act as sub), Top Subawardees (issued), with reliability badge if subaward coverage incomplete.
5. Capability Tag Workspace (Editor): Two-column region
   - Left: Draft Tags List (sortable by confidence, frequency). Each row: tag_name, frequency, confidence, source_count, actions (merge select checkbox, approve, delete).
   - Right: Approved Tags (grouped by class). Each tag pill: name, class color (core=blue, differentiator=purple, emerging=amber), confidence, last modified timestamp.
   - Merge Dialog: choose ≥2 draft tags -> new consolidated name -> resulting description (auto-suggest from aggregated sentences) -> confirm.
   - Classification Change Inline: dropdown on approved pill (updates counts & triggers version hash recalculation).
6. Subcontract Reliance Lens (Context Strip): Table summarizing top N draft/approved tags with high subcontract % (reliance score = subcontract_dollars_for_theme / total_theme_dollars). Provides quick “gap candidate” badge.
7. Transition Candidate Insight (Optional Panel – collapsed by default): Themes where we appear as sub for other primes + have growing self‑perform evidence.
8. (Placeholder) AI Capability Summary: Disabled state until local LLM summarizer endpoint active. Shows spec + button “Generate (Local)” -> disabled with tooltip if enrichment coverage score < threshold.
9. (Placeholder) Capability Chat: Disabled area referencing upcoming interactive chat (scope + local privacy note).
10. Version History Footer: Table (latest 5) with version_id (hash_short), timestamp, counts (core/diff/emerging), draft_count_remaining, triggering change (merge / approve / reclassify / manual_add). “View Diff” opens modal (see below).

Modal / Drawer Interactions

- Tag Merge Dialog (as above).
- Tag Diff Viewer: Show previous vs selected version; highlight added/removed tags & class changes (core→differentiator etc.). Export diff as JSON.
- Tag Evidence Modal: For a selected draft or approved tag, show snippet list (sentences or award IDs) that contributed; limited to top 20 by weight (others lazy-load).

Data Contracts (Core Objects)

1. DraftCapabilityTag: { id, tag, frequency, confidence (0–1), source_award_ids[], first_seen_date, last_seen_date }
2. ApprovedCapabilityTag: { id, tag, class (core|differentiator|emerging), confidence, frequency, merged_from_ids[], rationale_note?, created_at, updated_at }
3. TagVersionRecord: { version_id (sha256 of sorted approved tags + classes), created_at, counts: {core, differentiator, emerging, total_draft_remaining}, change_type, change_meta }
4. TagEvidenceSnippet (lazy loaded): { tag_id, award_id, snippet_text, source_type (prime|sub|external_doc|web_snippet), snippet_confidence }
5. SubcontractRelianceEntry: { tag_id, tag, subcontract_reliance_pct, dollars_prime, dollars_subcontracted, gap_candidate_flag }

Proposed Tables (DB Schema – capture schema, Human Readable)

- capability_tags_draft – Purpose: extracted tags pre‑approval. Key columns: id (pk), tag, frequency, confidence, source_award_ids (jsonb), first_seen_date, last_seen_date.
- capability_tags_final – Purpose: approved tags with class & merge lineage. Key columns: id (pk), tag, class, confidence, frequency, merged_from_ids (jsonb), rationale_note, created_at, updated_at.
- capability_tag_versions – Purpose: immutable version snapshots. Key columns: version_id (pk), created_at, counts_json, change_type, change_meta_json.
- capability_tag_evidence – Purpose: supporting sentences/snippets. Key columns: id (pk), tag_id (fk), award_id, snippet_text, source_type, snippet_confidence.
- capability_tag_reliance – Purpose: cached subcontract reliance metrics. Key columns: tag_id (fk), dollars_prime, dollars_subcontracted, subcontract_reliance_pct, gap_candidate_flag, computed_at.

Extraction & Refresh Logic (Pipeline Summary)

1. Collect corpus: award + subaward + enrichment text (same deterministic merge logic defined in 1.6 section).
2. Phrase extraction heuristic (frequency + POS filtering + NAICS/PSC alignment + curated allowlist/denylist).
3. Group similar phrases (lowercased, stem/lemmatized) -> cluster ID → representative phrase.
4. Compute frequency (award occurrences) + distribution diversity factor (spread across NAICS / agencies) -> preliminary confidence.
5. Insert/update draft tags (upsert on normalized tag text) with incremented frequency & recomputed confidence (weighted moving average).
6. Evidence selection: top N representative sentences per tag (hash & store only new to avoid duplication).
7. Subcontract reliance computation: join subaward theme mapping (future step) – for MVP, rely on progress placeholder (gap detection partial until theme-to-award robust mapping is built).
8. On each approve/merge/classify action: recalc version hash & insert capability_tag_versions row.

Interaction State Machine (Simplified)
State DraftView -> (Approve) -> ApprovedListUpdated -> VersionHashRecalc -> Idle.
State DraftView (Multi-Select) -> MergeDialogOpen -> Validate(NewName not duplicate) -> MergeCommit -> DraftRemoved + ApprovedInserted -> VersionHashRecalc -> Idle.
State ApprovedList -> Reclassify(ClassDropdownChange) -> UpdateRow -> VersionHashRecalc.
State ApprovedList -> ViewEvidence(tag_id) -> EvidenceModalOpen -> (Close) -> Return.

Performance Targets (Human Readable)

- Load page initial (metrics + ≤500 draft tags): <4s (precompute draft tag table; paginate evidence).
- Approve single tag action → updated counts render: <500ms (optimistic UI then server confirm).
- Merge 2–5 tags → new approved entry available: <1.5s (single transaction; reuse cluster data).
- Version diff modal open (last 2 versions): <800ms (prefetch last N version metadata on load).
- Evidence modal initial fetch (20 snippets): <1.2s (index on tag_id).

Acceptance Criteria (MVP)

1. Page loads with metrics + at least one of: draft or approved tag lists (empty state messages if none) without error.
2. Approving a draft tag removes it from draft list and adds to approved list with default class=core unless user changed class pre-commit.
3. Merge operation results in exactly one new approved tag and deletes the merged draft IDs; lineage stored in merged_from_ids.
4. Reclassifying an approved tag updates displayed counts and persists across reload (DB update test passes).
5. Version record written on every approve, merge, reclassify, or manual add; hash changes if and only if approved tag set or classes change.
6. Confidence and frequency values maintain monotonic frequency (never decreases) unless a reprocessing full rebuild occurs (explicit pipeline run).
7. Deleting a draft tag writes a version entry (change_type=delete_draft) but does NOT alter approved hash.
8. Evidence modal shows only snippets linked to selected tag; if >20 available, “Load More (Remaining X)” fetches next page.
9. Subcontract Reliance Lens shows at least a placeholder message if reliance data not yet computed (“Reliance analysis pending”).
10. All DB write operations logged with {user:'local', action, tag_id(s), version_id}.

Deferred / Future Enhancements (Human Readable)

- Quality: Semantic similarity threshold tuning with feedback adjustments.
- UX: Inline tag rename for approved tags (with lineage record).
- AI: Local LLM summarizer generates per‑tag 1–2 sentence descriptor (auditable).
- AI: Capability Chat integration with retrieval over approved tag evidence + related award summaries.
- Analytics: Capability growth trend sparkline (frequency by FY) adjacent to tag.
- Collaboration: Export/import stance JSON for sharing across machines.
- Governance: Tag deprecation flow (mark legacy, hidden from defaults).

Testing Strategy

1. Unit: merge logic (inputs tags A,B -> lineage recorded, freq aggregated), version hash deterministic, classification change updates counts.
2. Integration: page load with synthetic 300 draft tags (pagination), approve + merge flows, diff modal.
3. Property: hash unchanged when approving then reverting (delete newly approved + restore original draft) scenario – ensures version semantics correct (should produce different hashes since approved set changed sequence, document rationale in test comment).
4. Performance micro-bench: approve action p95 < target.

Instrumentation / Logging (Human Readable)

- tag_approve: fields – tag_id, new_class, old_state_hash, new_state_hash, frequency, confidence.
- tag_merge: fields – new_tag_id, merged_ids[], frequency_total, confidence_recalc, new_state_hash.
- tag_reclassify: fields – tag_id, from_class, to_class, new_state_hash.
- tag_delete_draft: fields – tag_id, new_state_hash.
- version_create: fields – version_id, counts_json, change_type.
- evidence_view: fields – tag_id, page_size, page_number.

Required New Backend Components (Lightweight)

1. TagRepository (CRUD + merge + version recording) – wraps SQL queries (avoid embedding SQL in Streamlit page). Functions: list_draft(limit,offset), list_approved(), approve(tag_id,class), merge(tag_ids,new_name,new_class), reclassify(tag_id,new_class), delete_draft(tag_id), get_version(version_id), list_versions(limit=5), list_evidence(tag_id,limit,offset), compute_version_hash().
2. TagVersionService – orchestrates write ops, calls repository, returns updated aggregates.
3. Extraction Pipeline Script `scripts/build_capability_tags.py` – runs steps 1–7 (Extraction & Refresh Logic) with idempotent upserts.
4. (Later) RelianceComputationJob – populates capability_tag_reliance (initial placeholder sets gap_candidate_flag=NULL).

UI Implementation Notes

- Keep Streamlit page under 350 LOC: move repository + service code to backend; keep only presenter + layout.
- All write actions go through a thin adapter returning success + updated counts (JSON) to allow potential future front-end swap.
- Use small optimistic update pattern: update UI immediately, then confirm; on failure revert and flash inline error.
- Color tokens reuse THEME; add color map for classes.

Security / Integrity Guardrails

1. Manual “Add Tag” requires rationale_note (>= 15 chars) or rejected.
2. Denylist (configurable) prevents certain generic words (“services”, “solutions”) from being approved unless manually overridden with rationale.
3. Merge operation prevented if resulting name duplicates existing approved tag (case-insensitive).
4. Evidence snippets sanitized (strip emails / potential PII) before storage.

Open Questions (Append to Section 5.12 List)

1. Minimum frequency threshold for drafting a tag (current heuristic?).
2. Do we persist draft tags that later fall below threshold after new data ingestion or mark as deprecated_draft?
3. How to surface conflicting tags (near duplicates approved separately) – automated similarity alert or manual review only?
4. Should emerging tags auto‑downgrade or upgrade after N periods of stability? (Temporal recategorization logic.)
5. Reliability scoring for subcontract reliance (insufficient data) – boolean flag vs scaled confidence weight?

Immediate Engineering Tasks (Add to 3.14 Action Checklist – Cross Reference)

- Implement TagRepository & TagVersionService (with unit tests).
- Create DB migrations for capability tables.
- Build extraction script (draft tag population) fed by existing award text.
- Implement Streamlit editor region (draft + approved) with approve/merge/reclassify flows.
- Add version diff modal + evidence modal (placeholder evidence now limited to award descriptions until external enrichment pipeline lands).
- Add logging events per Instrumentation table.

Completion Definition (for this Section’s Delivery)
All Acceptance Criteria satisfied; tests green; action checklist items above merged; documentation updated (this spec + README pointer); page accessible via navigation with stable load performance logs showing adherence to targets.

Outcome Benefit
Centralizes stance creation + reduces manual spreadsheets; standardizes downstream AI prompt templates and win theme generation inputs with traceable lineage.

---

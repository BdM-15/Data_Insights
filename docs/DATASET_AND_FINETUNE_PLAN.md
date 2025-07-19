# Data Insights LLM Fine-Tuning & Dataset Development Plan

## Objective

Develop a robust, prompt-friendly dataset and documentation to enable fine-tuning of local LLMs (Ollama Mistral, Llama3, etc.) for the Data Insights platform. The goal is to maximize tool-grounded, context-aware, and business-process-aligned agent performance for defense contracting analytics and capture management.

## Key Components

1. **Sample Data Structures**: Extract real schemas, data dictionaries, and representative records from the capture insights PostgreSQL database (see `/src/backend/data/models/data_models.py` and ETL scripts).
2. **Prompt/Response Examples**: Curate real user queries, tool call instructions, and agent responses from dashboard usage, `agent_test_cases.md`, and manual test scripts.
3. **Tool Calling Instructions**: Document tool schemas, input/output formats, and conversation loop patterns (see `AGENTIC_LLM_PLAN.md`, `capture_intelligence_agent.py`).
4. **Shipley Business Guide Integration**: Map Shipley capture milestones and business processes to data fields and agent workflows (see `CAPTUREINTEL.md`, `PLANNING.md`).
5. **External Datasets**: Identify and evaluate relevant datasets from HuggingFace and other sources for augmentation.
6. **Colab/Unslot/Platform Readiness**: Ensure dataset is structured for easy use in Google Colab, Unslot.ai, and other fine-tuning platforms.

## Action Steps

- [ ] Inventory and export sample schemas, data dictionaries, and representative records.
- [ ] Aggregate prompt/response pairs from real dashboard usage, test scripts, and `agent_test_cases.md`.
- [ ] Document tool schemas and agent conversation patterns.
- [ ] Map Shipley process steps to data and agent actions.
- [ ] Research and shortlist external datasets for augmentation.
- [ ] Structure all data in a prompt-friendly, platform-compatible format (JSONL, CSV, etc.).
- [ ] Document the full plan and update as progress is made.

## References

- `docs/AGENTIC_LLM_PLAN.md`: LLM architecture, prompt, and fine-tuning strategy
- `docs/CAPTUREINTEL.md`: Shipley process mapping and capture intelligence
- `docs/PLANNING.md`: Project vision and milestone planning
- `docs/TASKS.md`: Dataset, prompt, and testing tasks
- `src/backend/data/models/data_models.py`: Data schemas and validation models
- `agent_test_cases.md`: Example queries and agent test cases
- Dashboard code in `src/frontend/visualizations/` and `src/frontend/ai/`

---

**This document is the starting point for all dataset and fine-tuning work. Update as you progress.**

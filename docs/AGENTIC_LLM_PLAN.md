# Agentic LLM Architecture Plan (Dynamic, Intent-Driven)

## Phased Agentic LLM Integration Checklist

- [ ] 1. Document plan and requirements (**this section**)
- [ ] 2. Refactor backend for agentic, intent-driven pattern
- [ ] 3. Update prompt/context for dynamic tool selection (Llama3.2-8B as primary, Mistral-7B as fallback)
- [ ] 4. Add tool router for intent-based agent dispatch
- [ ] 5. Test with Llama3.2-8B and Mistral-7B (prompt engineering)
- [ ] 6. Fine-tune and phase in new models

---

## Requirements Summary

- All LLM inference is local (Ollama, CUDA, no external API calls)
- Modular, agent-based architecture: orchestrator LLM routes to specialized agents (data, visualization, document, web, analysis)
- Streamlit frontend, FastAPI backend, PostgreSQL for storage
- All context (user, session, page, tab, notes) is tracked and passed to agents
- Pydantic models for all agent APIs
- Designed for extensibility: new agents/tools can be added as business needs arise
- No hardcoded tool selection—LLM interprets user intent and selects tools dynamically
- All user actions and context are logged for observability and context enrichment

See also: `PLANNING.md`, `MODULARIZATION_AND_AI_PLAN.md`, and `TASKS.md` for supporting details and implementation notes.

## Vision

- The LLM acts as an agent, orchestrating tool use for data, visualization, notes, and document generation.
- The LLM interprets user intent from natural language prompts and autonomously selects the appropriate tool(s) to fulfill the request.
- The backend executes tool requests and returns results for the LLM to summarize, explain, or visualize.
- Users interact naturally—no need to reference tool names or technical details in their prompts.

## Tools (Capabilities)

- Data Query Tool: Query contract, agency, NAICS, and obligation data.
- Visualization Tool: Generate interactive charts and visualizations from contract data.
- Notes Tool: Retrieve, add, update, and delete user notes.
- Document Generator: Create capture profiles and milestone review documents.
- Analysis/Reasoning Tool: Provide strategic assessments and AI-augmented insights.

## LLM Output Format

- LLM receives the user prompt, schema, and available tools as context.
- LLM outputs a structured intent (e.g., JSON or natural language) describing what it wants to accomplish ("Show me a chart of top agencies by obligation for NAICS 541330").
- Backend parses the intent, routes to the correct tool, and returns results for the LLM to format and explain.
- LLM can chain tool calls if needed (e.g., query data, then generate a chart, then summarize findings).

## Dynamic Intent Recognition

- LLM is fine-tuned (or prompted) to:
  - Parse user intent from natural language.
  - Select the correct tool(s) without explicit user instruction.
  - Ask clarifying questions if the prompt is ambiguous.
  - Use only columns and tools available in the provided schema/context.

## Phased Migration

1. **Document plan and requirements** (this file)
2. **Refactor backend** to accept and execute tool requests based on LLM intent (not hardcoded logic)
3. **Update system prompt/context** to instruct the LLM to reason about user intent and select tools autonomously
4. **Implement tool router** in backend to dispatch LLM requests
5. **Test with current LLMs** (prompt engineering for intent extraction)
6. **Fine-tune LLMs** (Llama2, CodeLlama, Mistral) on your schema, queries, and dashboard logic for better intent recognition and tool use
7. **Phase in fine-tuned models** for each tool/capability

## Model Selection & Fine-Tuning Plan

- **Llama3.2-8B (Meta):**
  - Primary orchestrator/agentic LLM for intent extraction, reasoning, and tool selection.
  - Use for general chat, summarization, and as the main agentic model.
  - Fine-tune on your schema, queries, and workflows for best results.
- **Mistral-7B:**
  - Secondary orchestrator and fallback for reasoning, tool use, and summarization.
  - Use for multi-turn dialogue, instruction following, and as a backup agentic model.
  - Fine-tune for your schema and intent extraction if needed.
- **CodeLlama or StarCoder2 (if available):**
  - For code generation, dashboard queries, and visualization logic.
  - Fine-tune on your dashboard code and query patterns.
- **Training Data:**
  - Use real user prompts, dashboard queries, and tool usage logs for all fine-tuning.

## Milestones

- [ ] Document plan and requirements
- [ ] Refactor backend for agentic, intent-driven pattern
- [ ] Update prompt/context for dynamic tool selection (Llama3.2-8B as primary, Mistral-7B as fallback)
- [ ] Add tool router
- [ ] Test with Llama3.2-8B and Mistral-7B (prompt engineering)
- [ ] Fine-tune and phase in new models

## Example User Prompts (No Tool Names)

- "Show me the top 10 contracts for NAICS 541330 by total obligation."
- "Which agencies have the most expiring contracts this quarter?"
- "Summarize recent trends in Army contract spending."
- "Add a note to the dashboard about the new Navy opportunity."
- "Generate a capture profile for contract 12345."

## Example LLM Intent Output (for Backend)

```json
{
  "intent": "data_query",
  "filters": { "naics_code": "541330" },
  "sort_by": "federal_action_obligation",
  "order": "desc",
  "limit": 10
}
```

Or, for a chart:

```json
{
  "intent": "visualization",
  "chart_type": "bar",
  "x": "parent_award_agency_name",
  "y": "federal_action_obligation",
  "filters": { "naics_code": "541330" },
  "aggregate": "sum",
  "order": "desc",
  "limit": 10
}
```

---

**Summary:**

- Use **Llama3.2-8B** as your primary agentic/orchestrator LLM for intent extraction, reasoning, and tool selection.
- Use **Mistral-7B** as a secondary/fallback agentic LLM for reasoning and summarization.
- Use **CodeLlama** or **StarCoder2** for code and dashboard logic if available.
- Fine-tune models on your schema, queries, and workflows for best results.
- Users interact naturally; LLM interprets and reasons about intent.
- Backend executes tool requests based on LLM output.
- No need to start over—incrementally refactor and phase in agentic logic and models.

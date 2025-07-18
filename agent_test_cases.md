# Capture Intelligence Agent Test Cases

This document contains real-world test scenarios for the agentic workflow. Each case is designed to validate agent behavior, tool orchestration, LLM reasoning, and logging. These cases can be used for manual testing, automated test development, and future LLM fine-tuning.

---

## 1. Factual Database Query

**Scenario:** User asks for the total number of contracts in the database.

- **User Prompt:** "How many contracts are in the database?"
- **Expected Agent Behavior:**
  - Agent routes to the appropriate tool (e.g., `get_database_stats` or `query_database`).
  - Tool is called, output is validated.
  - Agent applies schema logic to distinguish contract types (e.g., basic contract, IDV/IDC, task/delivery order) using fields like `parent_award_id_piid`, `award_id_piid`, `modification_number`, and by analyzing the structure/prefix of `contract_award_unique_key` (e.g., `CONT_AWD_` for awards/modifications, `CONT_IDV_` for vehicles/orders).
  - Agent should use the pattern of `contract_award_unique_key` to help identify contract vehicles, but must also check `modification_number`:
    - For counting contracts, only include records where `modification_number = '0'` (base award).
    - For summing obligations, include all modifications (`modification_number` values) to capture the true cost, including deobligations, as this may differ from `potential_total_value_of_award`.
  - LLM summarizes the result (e.g., "There are 12,345 contracts in the database.")
- **LLM Fine-Tuning Note:**
  - Reinforce: Always use tool output for factual answers.
  - Reinforce: Reference and explain schema logic when summarizing results (e.g., clarify what is counted as a contract).
  - Avoid: Hallucinating numbers or making up data.
  - Avoid: Generalizing or misinterpreting contract types; always rely on schema logic provided by the agent/tool layer.

---

## 2. Table Schema Description

**Scenario:** User requests the schema for the "contracts" table.

- **User Prompt:** "Describe the schema for the contracts table."
- **Expected Agent Behavior:**
  - Agent calls `describe_table` with `table_name='contracts'`.
  - Tool returns column details; LLM formats and explains.
- **LLM Fine-Tuning Note:**
  - Reinforce: Use tool output, format as readable table or list.
  - Avoid: Guessing column names/types.

---

## 3. Visualization Request

**Scenario:** User asks for a spending trend chart by agency over the last 5 years.

- **User Prompt:** "Show me a chart of spending trends by agency for the last 5 years."
- **Expected Agent Behavior:**
  - Agent identifies visualization tool and relevant data query.
  - Tool(s) called, output injected.
  - LLM generates a summary and describes the chart.
- **LLM Fine-Tuning Note:**
  - Reinforce: Use real data, explain chart axes and trends.
  - Avoid: Inventing agencies or trends.

---

## 4. Expiring Contracts Alert

**Scenario:** User wants to know which contracts are expiring in the next 90 days.

- **User Prompt:** "Which contracts are expiring in the next 90 days?"
- **Expected Agent Behavior:**
  - Agent calls appropriate tool with date filter.
  - Tool returns expiring contracts; LLM summarizes and highlights urgent items.
- **LLM Fine-Tuning Note:**
  - Reinforce: Use tool output, highlight urgency.
  - Avoid: Making up contract details.

---

## 5. Non-Factual/Strategic Reasoning

**Scenario:** User asks for advice on improving win rate.

- **User Prompt:** "How can we improve our win rate in defense contracts?"
- **Expected Agent Behavior:**
  - Agent recognizes this is a reasoning/strategy question.
  - LLM provides best practices, references data if available, but does not invent stats.
- **LLM Fine-Tuning Note:**
  - Reinforce: Use reasoning, reference real data if possible.
  - Avoid: Making up statistics or guarantees.

---

## 6. Ambiguous Prompt Handling

**Scenario:** User asks, "Show me the top performers."

- **User Prompt:** "Show me the top performers."
- **Expected Agent Behavior:**
  - Agent asks clarifying questions (e.g., "Do you mean top contractors, agencies, or NAICS codes?")
  - Once clarified, agent proceeds with tool call.
- **LLM Fine-Tuning Note:**
  - Reinforce: Ask for clarification when prompt is ambiguous.
  - Avoid: Making assumptions without user input.

---

## 7. Tool Error Handling

**Scenario:** Tool call fails due to database connection error.

- **User Prompt:** "List all agencies."
- **Expected Agent Behavior:**
  - Agent attempts tool call, catches error.
  - LLM explains the error to the user and suggests retrying or checking system status.
- **LLM Fine-Tuning Note:**
  - Reinforce: Transparent error reporting, no hallucination.
  - Avoid: Pretending the tool succeeded.

---

## 8. Logging and Audit Trail

**Scenario:** After each interaction, verify that all details are logged in `app_logs.agent_interaction_log`.

- **User Prompt:** Any of the above.
- **Expected Agent Behavior:**
  - All prompts, tool calls, results, LLM outputs, errors, and context are logged.
- **LLM Fine-Tuning Note:**
  - Reinforce: Complete, accurate logging for every step.

---

## 9. Edge Case: No Data Available

**Scenario:** User asks for contracts expiring in the next 7 days, but there are none.

- **User Prompt:** "Which contracts are expiring in the next 7 days?"
- **Expected Agent Behavior:**
  - Agent calls tool, receives empty result.
  - LLM explains that no contracts are expiring in that period.
- **LLM Fine-Tuning Note:**
  - Reinforce: Honest reporting of no data, no invention.

---

## 10. Multi-Tool Orchestration

**Scenario:** User asks for a summary and visualization of top NAICS codes by obligation.

- **User Prompt:** "Summarize and visualize the top NAICS codes by obligation."
- **Expected Agent Behavior:**
  - Agent orchestrates multiple tool calls (summary + visualization).
  - LLM combines outputs, explains findings and chart.
- **LLM Fine-Tuning Note:**
  - Reinforce: Multi-step reasoning, clear explanation.
  - Avoid: Mixing up tool outputs or inventing data.

---

# Notes for LLM Fine-Tuning

- Always use tool output for factual/database answers.
- Never hallucinate data, statistics, or details.
- Ask clarifying questions for ambiguous prompts.
- Report errors transparently.
- Summarize, explain, and contextualize tool output for the user.
- Log every step for auditability.

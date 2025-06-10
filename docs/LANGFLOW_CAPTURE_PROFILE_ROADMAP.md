# Langflow Capture Profile Generation Roadmap

## Overview

This document provides a step-by-step guide to building a Langflow workflow for capture managers, enabling automated research, document parsing, and capture profile generation using local LLMs, the Langflow MCP server, and integrations with the SAM.gov API and PostgreSQL vector search. All processing is local for privacy and compliance.

---

## Prerequisites

Before building the workflow in Langflow, ensure the following:

- **Langflow is installed and running** (see [Langflow Docs](https://docs.langflow.org/)).
- **Ollama is installed** with local models (e.g., `mistral`, `llama2`, `nomic-embed-text`).
- **PostgreSQL** is running with `pgvector` extension enabled for vector storage.
- **SAM.gov API key** is available for querying opportunities.
- **Document parsing tools** (e.g., PDF, DOCX parsers) are available as Python modules or via Langflow tool nodes.
- **MCP server** is set up for agent orchestration (see [Langflow MCP Server Docs](https://docs.langflow.org/mcp-server)).
- **All required Python packages** are installed in your environment.

---

## Optional: Dockerized Deployment for Langflow Workflow

While not strictly required, using Docker and Docker Compose is highly recommended for this workflow, especially for production, team environments, or when you want to ensure consistent, reproducible deployments.

### Why Use Docker?

- **Environment Consistency:** All dependencies (Langflow, Ollama, PostgreSQL with pgvector, document parsers, MCP server, etc.) are installed and configured the same way on any machine.
- **Isolation:** Keeps your AI/LLM stack, database, and supporting tools separate from your host OS, avoiding version conflicts.
- **Reproducibility:** Makes it easy to share, deploy, and update your workflow across teams or servers.
- **Easy Startup/Shutdown:** All services can be started or stopped with a single command.

### What to Include in Docker Compose

- **Langflow server** (the main workflow orchestrator)
- **Ollama** (for local LLMs)
- **PostgreSQL** (with `pgvector` extension enabled)
- **MCP server** (if not running as a separate service)
- **Any custom document parsing or ETL services**

### Example `docker-compose.yml` Structure

```yaml
version: "3.8"
services:
  langflow:
    image: langflow/langflow:latest
    ports:
      - "7860:7860"
    environment:
      - ... # Add environment variables as needed
    depends_on:
      - postgres
      - ollama
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  postgres:
    image: ankane/pgvector
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: data_insights
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  mcp-server:
    build: ./github-mcp-server
    ports:
      - "8080:8080"
    depends_on:
      - postgres
volumes:
  pgdata:
  ollama_data:
```

> **Note:**
>
> - You may need to adjust image names, build contexts, and environment variables for your specific setup.
> - If you have custom document parsing or ETL services, add them as additional services.
> - For local development, you can still run any of these services outside Docker if you prefer.

### How to Use

1. Create a `docker-compose.yml` file in your project root (see above for a template).
2. Place any custom Dockerfiles (e.g., for MCP server) in the appropriate directories.
3. Run `docker-compose up --build` from your project root to start all services.
4. Access Langflow at [http://localhost:7860](http://localhost:7860) (or the port you specify).
5. Stop all services with `docker-compose down`.

### Additional Tips

- Use Docker secrets or `.env` files for sensitive configuration.
- For production, consider using Docker volumes for persistent data.
- You can scale or update individual services without affecting the rest of the stack.

---

---

## Full Langflow Node-by-Node JSON Export

```json
{
  "name": "Capture Profile Generation Workflow",
  "description": "Langflow workflow for capture managers to gather, analyze, and synthesize public opportunity data into actionable capture profiles using local LLMs, web tools, and vector search.",
  "nodes": [
    {
      "id": "input_query",
      "type": "Input",
      "label": "Opportunity Search Input",
      "description": "User provides keywords, NAICS, agency, or opportunity name."
    },
    {
      "id": "samgov_search",
      "type": "Tool",
      "label": "SAM.gov Search",
      "tool": "bravewebsearch",
      "params": {
        "query": "{input_query} site:sam.gov inactive solicitations"
      },
      "description": "Searches SAM.gov for inactive/archived solicitations matching the input."
    },
    {
      "id": "samgov_rfp_scraper",
      "type": "Tool",
      "label": "RFP Document Scraper",
      "tool": "crawl4ai",
      "params": {
        "urls": "{samgov_search.results.urls}"
      },
      "description": "Downloads and extracts text from RFPs, SOWs, and attachments."
    },
    {
      "id": "rfp_vector_search",
      "type": "Tool",
      "label": "RFP Vector Search",
      "tool": "langflow_postgresql",
      "params": {
        "query": "{input_query}",
        "table": "rfp_vectors"
      },
      "description": "Searches vectorized RFPs for similar requirements, evaluation criteria, and clauses."
    },
    {
      "id": "historical_award_vector_search",
      "type": "Tool",
      "label": "Historical Award Vector Search",
      "tool": "langflow_postgresql",
      "params": {
        "query": "{input_query}",
        "table": "award_vectors"
      },
      "description": "Finds similar historical awards, primes, and sub-awards for context."
    },
    {
      "id": "web_intel_agent",
      "type": "Agent",
      "label": "Web Intelligence Agent",
      "model": "ollama/mistral",
      "params": {
        "context": "{samgov_rfp_scraper.text} {rfp_vector_search.results} {historical_award_vector_search.results}"
      },
      "description": "Summarizes and extracts key requirements, evaluation factors, and trends from RFPs and awards."
    },
    {
      "id": "market_research_agent",
      "type": "Agent",
      "label": "Market Research Agent",
      "model": "ollama/llama2",
      "params": {
        "context": "{web_intel_agent.summary}",
        "task": "Identify top competitors, teaming partners, and pricing trends."
      }
    },
    {
      "id": "capture_profile_generator",
      "type": "Agent",
      "label": "Capture Profile Generator",
      "model": "ollama/llama2",
      "params": {
        "context": "{web_intel_agent.summary} {market_research_agent.summary}",
        "task": "Draft a capture profile including opportunity summary, requirements, evaluation criteria, competitive landscape, teaming, and win themes."
      }
    },
    {
      "id": "document_creator",
      "type": "Tool",
      "label": "Document Creator",
      "tool": "mcd-alchemy",
      "params": {
        "content": "{capture_profile_generator.profile}",
        "format": "docx"
      },
      "description": "Generates a Word document with the capture profile."
    },
    {
      "id": "chatbot",
      "type": "Agent",
      "label": "Capture Chatbot",
      "model": "ollama/mistral",
      "params": {
        "context": "{capture_profile_generator.profile}",
        "tools": ["calculator", "web_intel_agent", "market_research_agent"],
        "task": "Answer user questions about the opportunity, RFP, or competitive landscape."
      }
    },
    {
      "id": "output",
      "type": "Output",
      "label": "Profile & Chat Output",
      "params": {
        "profile_doc": "{document_creator.docx}",
        "chat_interface": "{chatbot}"
      }
    }
  ],
  "edges": [
    { "from": "input_query", "to": "samgov_search" },
    { "from": "samgov_search", "to": "samgov_rfp_scraper" },
    { "from": "samgov_rfp_scraper", "to": "rfp_vector_search" },
    { "from": "input_query", "to": "rfp_vector_search" },
    { "from": "input_query", "to": "historical_award_vector_search" },
    { "from": "samgov_rfp_scraper", "to": "web_intel_agent" },
    { "from": "rfp_vector_search", "to": "web_intel_agent" },
    { "from": "historical_award_vector_search", "to": "web_intel_agent" },
    { "from": "web_intel_agent", "to": "market_research_agent" },
    { "from": "market_research_agent", "to": "capture_profile_generator" },
    { "from": "web_intel_agent", "to": "capture_profile_generator" },
    { "from": "capture_profile_generator", "to": "document_creator" },
    { "from": "capture_profile_generator", "to": "chatbot" },
    { "from": "document_creator", "to": "output" },
    { "from": "chatbot", "to": "output" }
  ]
}
```

---

## Step-by-Step Instructions for Building the Workflow in Langflow

### 1. Launch Langflow

- Start Langflow via your preferred method (e.g., `langflow run`).
- Open the Langflow IDE in your browser.

### 2. Add Nodes

#### a. Input Node

- **Type:** Input
- **Label:** Opportunity Search Input
- **Purpose:** User enters keywords, NAICS, agency, or opportunity name.

#### b. SAM.gov Search Node

- **Type:** Tool
- **Label:** SAM.gov Search
- **Tool:** bravewebsearch (or use a custom tool node for the SAM.gov API)
- **Params:**
  - `query`: `{input_query} site:sam.gov inactive solicitations`
- **Purpose:** Finds relevant opportunities on SAM.gov.

#### c. RFP Document Scraper Node

- **Type:** Tool
- **Label:** RFP Document Scraper
- **Tool:** crawl4ai (or your document downloader/parser)
- **Params:**
  - `urls`: `{samgov_search.results.urls}`
- **Purpose:** Downloads and extracts text from RFPs and attachments.

#### d. RFP Vector Search Node

- **Type:** Tool
- **Label:** RFP Vector Search
- **Tool:** langflow_postgresql (or your vector DB search tool)
- **Params:**
  - `query`: `{input_query}`
  - `table`: `rfp_vectors`
- **Purpose:** Finds similar RFPs for context.

#### e. Historical Award Vector Search Node

- **Type:** Tool
- **Label:** Historical Award Vector Search
- **Tool:** langflow_postgresql
- **Params:**
  - `query`: `{input_query}`
  - `table`: `award_vectors`
- **Purpose:** Finds similar historical awards.

#### f. Web Intelligence Agent Node

- **Type:** Agent
- **Label:** Web Intelligence Agent
- **Model:** ollama/mistral
- **Params:**
  - `context`: `{samgov_rfp_scraper.text} {rfp_vector_search.results} {historical_award_vector_search.results}`
- **Purpose:** Summarizes and extracts key requirements and trends.

#### g. Market Research Agent Node

- **Type:** Agent
- **Label:** Market Research Agent
- **Model:** ollama/llama2
- **Params:**
  - `context`: `{web_intel_agent.summary}`
  - `task`: "Identify top competitors, teaming partners, and pricing trends."
- **Purpose:** Provides market/competitive analysis.

#### h. Capture Profile Generator Node

- **Type:** Agent
- **Label:** Capture Profile Generator
- **Model:** ollama/llama2
- **Params:**
  - `context`: `{web_intel_agent.summary} {market_research_agent.summary}`
  - `task`: "Draft a capture profile including opportunity summary, requirements, evaluation criteria, competitive landscape, teaming, and win themes."
- **Purpose:** Synthesizes all data into a structured capture profile.

#### i. Document Creator Node

- **Type:** Tool
- **Label:** Document Creator
- **Tool:** mcd-alchemy (or your document generation tool)
- **Params:**
  - `content`: `{capture_profile_generator.profile}`
  - `format`: `docx`
- **Purpose:** Generates a Word document with the capture profile.

#### j. Capture Chatbot Node

- **Type:** Agent
- **Label:** Capture Chatbot
- **Model:** ollama/mistral
- **Params:**
  - `context`: `{capture_profile_generator.profile}`
  - `tools`: ["calculator", "web_intel_agent", "market_research_agent"]
  - `task`: "Answer user questions about the opportunity, RFP, or competitive landscape."
- **Purpose:** Provides interactive Q&A.

#### k. Output Node

- **Type:** Output
- **Label:** Profile & Chat Output
- **Params:**
  - `profile_doc`: `{document_creator.docx}`
  - `chat_interface`: `{chatbot}`
- **Purpose:** Final output for user download and chat.

---

### 3. Connect the Nodes

**Explicit List of All Node Connections (Edges)**

1. `input_query` → `samgov_search`

   - The output of the `input_query` node is connected to the input of the `samgov_search` node.

2. `samgov_search` → `samgov_rfp_scraper`

   - The output of the `samgov_search` node is connected to the input of the `samgov_rfp_scraper` node.

3. `samgov_rfp_scraper` → `rfp_vector_search`

   - The output of the `samgov_rfp_scraper` node is connected to the input of the `rfp_vector_search` node.

4. `input_query` → `rfp_vector_search`

   - The output of the `input_query` node is also connected to the input of the `rfp_vector_search` node.

5. `input_query` → `historical_award_vector_search`

   - The output of the `input_query` node is connected to the input of the `historical_award_vector_search` node.

6. `samgov_rfp_scraper` → `web_intel_agent`

   - The output of the `samgov_rfp_scraper` node is connected to the input of the `web_intel_agent` node.

7. `rfp_vector_search` → `web_intel_agent`

   - The output of the `rfp_vector_search` node is connected to the input of the `web_intel_agent` node.

8. `historical_award_vector_search` → `web_intel_agent`

   - The output of the `historical_award_vector_search` node is connected to the input of the `web_intel_agent` node.

9. `web_intel_agent` → `market_research_agent`

   - The output of the `web_intel_agent` node is connected to the input of the `market_research_agent` node.

10. `market_research_agent` → `capture_profile_generator`

    - The output of the `market_research_agent` node is connected to the input of the `capture_profile_generator` node.

11. `web_intel_agent` → `capture_profile_generator`

    - The output of the `web_intel_agent` node is also connected to the input of the `capture_profile_generator` node.

12. `capture_profile_generator` → `document_creator`

    - The output of the `capture_profile_generator` node is connected to the input of the `document_creator` node.

13. `capture_profile_generator` → `chatbot`

    - The output of the `capture_profile_generator` node is connected to the input of the `chatbot` node.

14. `document_creator` → `output`

    - The output of the `document_creator` node is connected to the input of the `output` node.

15. `chatbot` → `output`
    - The output of the `chatbot` node is connected to the input of the `output` node.

**Summary Table**

| From Node                      | To Node                        |
| ------------------------------ | ------------------------------ |
| input_query                    | samgov_search                  |
| samgov_search                  | samgov_rfp_scraper             |
| samgov_rfp_scraper             | rfp_vector_search              |
| input_query                    | rfp_vector_search              |
| input_query                    | historical_award_vector_search |
| samgov_rfp_scraper             | web_intel_agent                |
| rfp_vector_search              | web_intel_agent                |
| historical_award_vector_search | web_intel_agent                |
| web_intel_agent                | market_research_agent          |
| market_research_agent          | capture_profile_generator      |
| web_intel_agent                | capture_profile_generator      |
| capture_profile_generator      | document_creator               |
| capture_profile_generator      | chatbot                        |
| document_creator               | output                         |
| chatbot                        | output                         |

---

### 4. Node Configuration Tips

- **For each node, set the label and parameters as described above.**
- **For tool/agent nodes, select the correct tool or model from the dropdown or enter the custom tool name.**
- **For context/params fields, use curly braces `{}` to reference outputs from previous nodes.**
- **Ensure all required Python packages and models are installed and available to Langflow.**
- **Test each node individually before chaining the full workflow.**

---

### 5. Additional Notes

- **SAM.gov API Integration:** For production, replace the `bravewebsearch` node with a custom tool node that calls the [SAM.gov API](https://open.gsa.gov/api/get-opportunities-public-api/) directly, parses the JSON, and outputs opportunity metadata and document links.
- **Document Parsing:** Ensure your document parser can handle all relevant file types (PDF, DOCX, TXT).
- **Vectorization:** Use a local embedding model (e.g., `nomic-embed-text`) and store vectors in PostgreSQL with `pgvector`.
- **MCP Server:** Configure the MCP server to orchestrate agent/tool selection as needed.
- **Security:** All data and processing should remain local for compliance.

---

## References

- [Langflow Documentation](https://docs.langflow.org/)
- [Langflow MCP Server](https://docs.langflow.org/mcp-server)
- [SAM.gov Get Opportunities Public API](https://open.gsa.gov/api/get-opportunities-public-api/)
- [Shipley Capture Guide](./Shipley%20Capture%20Guide..txt)
- [PLANNING.md](./PLANNING.md)
- [MODULARIZATION_AND_AI_PLAN.md](./MODULARIZATION_AND_AI_PLAN.md)

---

_Last updated: 2025-06-01_

# MCP Server Integration for Langflow Workflows

## Overview

This document explains how to modularize your Langflow workflow using MCP (Model Context Protocol) servers for tools that are not built into Langflow. It covers why and how to use MCP servers, how to orchestrate them with Docker Compose, and what steps to follow for a robust, maintainable architecture.

---

## Why Use MCP Servers?

- **Separation of Concerns:** Each data fetcher or tool (e.g., Crawl4AI, custom SAM.gov fetcher) runs as its own service.
- **Scalability:** Add, update, or scale services independently.
- **Reusability:** Other workflows or apps can use the same MCP servers.
- **Security:** Credentials and sensitive logic are isolated per service.
- **Easy Orchestration:** Use Docker Compose to start/stop all services with one command.

---

## Recommended Implementation Steps

1. **Build MCP Servers First**

   - For each external tool (e.g., Crawl4AI, custom document parser, SAM.gov API fetcher), create an MCP server.
   - Each MCP server exposes a standard API (usually HTTP/JSON) for Langflow to call.
   - Example: Run Crawl4AI as an MCP server with `crawl4ai mcp-server --host 0.0.0.0 --port 8081`.

2. **Create a Docker Compose File**
   - Add each MCP server as a service in `docker-compose.yml`.
   - Example:

```yaml
version: "3.8"
services:
  crawl4ai-mcp:
    image: unclecode/crawl4ai:latest
    command: crawl4ai mcp-server --host 0.0.0.0 --port 8081
    ports:
      - "8081:8081"
    volumes:
      - ./crawl4ai_data:/app/data
  # Add other MCP servers here
```

3. **Configure Langflow to Use MCP Servers**

   - In your Langflow workflow, set the tool name to match the MCP server (e.g., `crawl4ai`).
   - Ensure Langflow is configured to route requests to the correct MCP server endpoint.
   - For built-in tools (e.g., vector search, Ollama agents), no extra setup is needed.

4. **Test Each MCP Server**
   - Start all services with `docker-compose up` (or via Podman if preferred).
   - Test each tool node in Langflow individually before chaining the full workflow.

---

## Node-by-Node Implementation Checklist

| Node                           | Tool/Model          | What to Do                                                                    |
| ------------------------------ | ------------------- | ----------------------------------------------------------------------------- |
| samgov_search                  | bravewebsearch      | Use built-in or implement custom tool for SAM.gov API search                  |
| samgov_rfp_scraper             | crawl4ai            | Run Crawl4AI MCP server and connect via MCP (recommended); no .py file needed |
| rfp_vector_search              | langflow_postgresql | Ensure pgvector is enabled; configure Langflow to connect to your DB          |
| historical_award_vector_search | langflow_postgresql | Same as above                                                                 |
| web_intel_agent                | ollama/mistral      | Ensure Ollama is running with model; configure Langflow to use local LLM      |
| market_research_agent          | ollama/llama2       | Same as above                                                                 |
| capture_profile_generator      | ollama/llama2       | Same as above                                                                 |
| document_creator               | mcd-alchemy         | Use built-in or implement custom tool for docx generation                     |
| chatbot                        | ollama/mistral      | Same as above                                                                 |
| output                         | Output              | No extra work                                                                 |

---

## Additional Tips

- Use Docker secrets or `.env` files for sensitive configuration.
- For production, use Docker volumes for persistent data.
- You can scale or update individual services without affecting the rest of the stack.
- For local development, you can run any of these services outside Docker if you prefer.

---

## References

- [Langflow Documentation](https://docs.langflow.org/)
- [Langflow MCP Server](https://docs.langflow.org/mcp-server)
- [Crawl4AI GitHub](https://github.com/unclecode/crawl4ai)
- [SAM.gov Get Opportunities Public API](https://open.gsa.gov/api/get-opportunities-public-api/)
- [Ollama](https://ollama.com/)

---

**Best Practice:**

- Build and test your MCP servers first, then integrate them into your Langflow workflow using Docker Compose for orchestration.

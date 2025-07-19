---
config:
  layout: elk
  theme: neo-dark
---
flowchart LR
User["User Prompt"] --> Agent["Agent (Controller)"]
Agent --> LLM1["LLM (Tool Decision)"]
Agent --> MCP["MCP Server<br/>(Tool Execution)"]
Agent --> LLM2["LLM (Post-Processing/Synthesis)"]
Agent --> Response["Final Response to User"]
LLM1 --> ToolCheck{"Tool Call Needed?"}
ToolCheck -- Yes --> Agent
MCP --> Agent
ToolCheck -- No --> LLM2
LLM2 --> Agent

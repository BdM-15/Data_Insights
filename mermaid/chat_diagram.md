flowchart TD
    A[Streamlit UI<br>Market Overview Tab] -->|User submits question| B[MCP Chat Server (FastAPI)]
    B --> C[LLM Interface<br>(Ollama: Mistral/Llama-3 for Q&A,<br>Code Llama for code)]
    B --> D[Database Access<br>(capture_insights)]
    B --> E[Logger<br>(app_logs.chat_logs)]
    C -->|LLM response/code| B
    D -->|Data for context| B
    B -->|Answer/Visualization| A
    E -->|Log entry| F[app_logs.chat_logs table]
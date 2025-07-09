"""
Reusable Streamlit component for Data_Insights Chat/Notes/Visualization UI.

- Use this module to render the chat, notes, and visualization UI in any Streamlit page.
- All backend API calls and session context are handled internally.

Usage:
    from src.frontend.components.chat_with_data import render_chat_with_data
    render_chat_with_data(page="market_overview", tab="main")
"""

import streamlit as st
import requests
import uuid

API_URL = "http://localhost:8001"  # Adjust if backend runs elsewhere



# --- Notes feature is currently disabled. To re-enable, uncomment the render_notes_section function and its usages below. ---
# @st.fragment
# def render_notes_section(page, tab, user_id, session_id):
#     """
#     Render the notes UI for the Data_Insights app.
#     ... (full implementation commented out) ...
#     """
#     pass

def render_chat_with_data(page: str = "market_overview", tab: str = "main"):
    """
    Render the chat, notes, and visualization UI for the Data_Insights app.

    Args:
        page: Page context for notes/chat logging
        tab: Tab context for notes/chat logging
    """
    # --- Session and user context ---
    session_id = st.session_state.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        st.session_state["session_id"] = session_id
    user_id = st.session_state.get("user_id", "demo_user")

    # render_notes_section(page, tab, user_id, session_id)  # Notes feature disabled

    # --- Chat UI (fragmented for partial rerun, no full rerun) ---
    @st.fragment
    def chat_section():
        st.subheader("Ask a question about your data")
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        if "chat_input" not in st.session_state:
            st.session_state["chat_input"] = ""

        # Chat input form (so only this fragment reruns)
        with st.form("chat_input_form", clear_on_submit=True):
            user_prompt = st.text_input("Your question:", st.session_state["chat_input"], key="chat_user_prompt")
            # Optional: model selector (default: mistral)
            model = st.selectbox("Model", ["mistral", "llama2", "codellama"], key="chat_model")
            send_clicked = st.form_submit_button("Send")
            if send_clicked and user_prompt.strip():
                # Fetch notes for context
                notes_resp = requests.get(f"{API_URL}/notes", params={"page": page, "tab": tab, "user_id": user_id, "session_id": session_id})
                notes = notes_resp.json().get("notes", []) if notes_resp.ok else []
                notes_text = "\n".join([n["note_text"] for n in notes])

                # --- System prompt logic: only send on first user message ---
                system_prompt = None
                if not st.session_state["chat_history"]:
                    system_prompt = (
                        "You are Roberto, an expert business intelligence assistant for defense contractors, specializing in logistics, operations, maintenance, and technology solutions. "
                        "Your primary role is to help users explore, analyze, and visualize government contract data, provide strategic insights, and support capture management and business development.\n"
                        "\n"
                        "Your capabilities and tools:\n"
                        "- You have access to all contract data, user notes, and context from the Data_Insights platform.\n"
                        "- You can use the following MCP tools:\n"
                        "  - Web Intelligence Scraper: For gathering up-to-date market research and external intelligence.\n"
                        "  - Document Creator/Editor: For generating and editing reports, capture profiles, and strategic documents.\n"
                        "  - Visualization Tool: For creating interactive charts, graphs, and visual summaries of data.\n"
                        "  - Analysis/Reasoning Tool: For advanced data analysis, opportunity qualification, and strategic recommendations.\n"
                        "  - LLM Models: You can use local models such as Mistral, Llama2, and CodeLlama for natural language understanding and generation.\n"
                        "\n"
                        "How to use your tools:\n"
                        "- Use the Visualization Tool whenever a user asks for a chart, graph, or visual summary.\n"
                        "- Use the Web Intelligence Scraper for questions about market trends, competitors, or external data.\n"
                        "- Use the Document Creator/Editor for requests to generate or edit reports, capture profiles, or summaries.\n"
                        "- Use the Analysis/Reasoning Tool for deep-dive analysis, opportunity scoring, or strategic advice.\n"
                        "- Always combine user notes and contract data with your responses for maximum relevance.\n"
                        "\n"
                        "Reasoning and response structure:\n"
                        "1. Reflect: Carefully consider the user’s question and context.\n"
                        "2. Explore: Investigate multiple approaches or tools that could help.\n"
                        "3. Analyze: Break down the chosen approach, referencing data, notes, and tools.\n"
                        "4. Solve: Work through each step methodically, using MCP tools as needed.\n"
                        "5. Observe: Check your answer for errors, inconsistencies, or missing context.\n"
                        "6. Notify: Present your answer clearly, justifying your reasoning and including any relevant visualizations or documents.\n"
                        "\n"
                        "General guidelines:\n"
                        "- Always keep all data processing and AI inference local for privacy and security.\n"
                        "- Never use external APIs or cloud services.\n"
                        "- Prioritize clear, actionable, and well-justified answers.\n"
                        "- If a visualization or document is generated, include it directly in your response.\n"
                        "- If you need more information, ask clarifying questions.\n"
                    )

                payload = {
                    "user_prompt": user_prompt,
                    "page": page,
                    "tab": tab,
                    "session_id": session_id,
                    "user_id": user_id,
                    "notes": notes_text,
                    "model": model
                }
                if system_prompt:
                    payload["system_prompt"] = system_prompt

                # Use MCP LLM endpoint for real LLM response
                resp = requests.post(f"{API_URL}/chat", json=payload)
                if resp.ok:
                    answer = resp.json().get("answer", "[No answer returned]")
                    vis_url = resp.json().get("visualization_url")
                    st.session_state["chat_history"].append({"user": user_prompt, "bot": answer, "visualization_url": vis_url})
                else:
                    st.session_state["chat_history"].append({"user": user_prompt, "bot": "[Error: Backend unavailable]", "visualization_url": None})
                st.session_state["chat_input"] = ""
            else:
                st.session_state["chat_input"] = user_prompt

        # Display chat history (latest at bottom)
        for entry in st.session_state["chat_history"]:
            st.markdown(f"**You:** {entry['user']}")
            st.markdown(f"**Roberto:** {entry['bot']}")
            if entry.get("visualization_url"):
                st.image(entry["visualization_url"], caption="Visualization", use_column_width=True)

    chat_section()
    st.divider()


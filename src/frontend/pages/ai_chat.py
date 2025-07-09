
import streamlit as st
import time
import requests
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes

def check_and_handle_session_timeout():
    """
    Checks if the session has timed out due to inactivity.
    If so, triggers backend soft-delete for all notes in this session.
    """
    now = time.time()
    last_active = st.session_state.get("last_activity_ts", now)
    session_id = st.session_state.get("session_id")  # Should be set at login/session start
    user_id = st.session_state.get("user_id")        # Should be set at login/session start

    if now - last_active > SESSION_TIMEOUT_SECONDS:
        # Reason: Session timed out, trigger backend bulk soft-delete for this session
        if session_id and user_id:
            try:
                response = requests.post(
                    "http://localhost:8001/notes/soft_delete_all",
                    json={"session_id": session_id, "user_id": user_id},
                    timeout=5
                )
                if response.status_code == 200:
                    st.session_state["notes"] = []
                    st.info("Session expired. All notes have been archived (soft deleted).")
            except Exception as e:
                st.warning(f"Failed to archive notes on session timeout: {e}")
        # Reset last activity to now to avoid repeated calls
        st.session_state["last_activity_ts"] = now
    else:
        # Update last activity timestamp
        st.session_state["last_activity_ts"] = now



# --- Notes feature is currently disabled. To re-enable, uncomment the notes_fragment function and its usages below. ---
# @st.fragment
# def notes_fragment():
#     st.subheader("Your Notes")
#     ... (full implementation commented out) ...
#     pass

# --- Chat Feature as Fragment ---
@st.fragment
def chat_fragment():
    st.subheader("Chat with the Data")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display chat history (top to bottom)
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"<span style='color:#4B8BBE'><b>AI:</b> {msg['content']}</span>", unsafe_allow_html=True)

    # Chat input at the bottom
    user_input = st.text_input("Ask a question about the data, contracts, or trends:", key="chat_input")
    send = st.button("Send", key="send_button")

    if send and user_input.strip():
        # Append user message
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        # Placeholder for AI response (replace with backend call)
        ai_response = "[AI response will appear here. Integration with agentic LLM backend is coming soon.]"
        st.session_state["chat_history"].append({"role": "ai", "content": ai_response})



def main():
    """
    Streamlit page entry point for AI Chat with the Data.
    Sets up theme, description, and renders notes and chat fragments.
    """
    # Automatic session timeout/soft-delete check
    check_and_handle_session_timeout()
    # Inject custom theme CSS for visual consistency
    st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)
    st.title("🤖 AI Chat with the Data")
    st.markdown(
        """
        **Welcome to the AI Chat with the Data!**

        This page lets you interact with an advanced AI assistant powered by multiple local LLMs running via Ollama. The system uses an "orchestrator" LLM (Llama3.2-8B or Mistral-7B) to interpret your intent and route requests to specialized models for code, visualization, and analysis.

        - **Data Sources:** Capture Insights Database - usaspending_prime_awards and usaspending_subawards tables.
        - **Ollama** runs all models locally for privacy and performance (no external API calls).
        - **Orchestrator LLM** (Llama3.2-8B or Mistral-7B) interprets your question and decides which tool or model to use.
        - **Specialized models** (e.g., CodeLlama, StarCoder2) handle code generation, data queries, and visualizations as needed.
        - **Fine-tuned Models:** The LLMs have been fine-tuned on defense contracting, logistics, and business intelligence data to provide more relevant, actionable insights and context-aware responses.
        - Ask about spending trends, top agencies, expiring contracts, or any other business intelligence question.
        - The AI has access to all available data, not just the current dashboard or filtered view.
        - Use natural language—no need for technical terms or SQL.
        - Add notes to capture your findings or ideas.

        _For context-specific analysis, use the other dashboard pages._
        """
    )
    # notes_fragment()  # Notes feature disabled
    st.markdown("---")
    chat_fragment()

if __name__ == "__main__":
    main()

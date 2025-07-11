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

def get_agentic_response(user_input, context=None):
    try:
        # Use the new flexible routing endpoint with enhanced context
        payload = {
            "prompt": user_input, 
            "context": context or {},
            "user_id": st.session_state.get("user_id", "streamlit_user"),
            "session_id": st.session_state.get("session_id", "default_session"),
            "page": "ai_chat",
            "tab": "chat"
        }
        
        # Use the main orchestrator route with dynamic tool discovery
        response = requests.post("http://localhost:8001/orchestrator/route", json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", str(data))
        else:
            # Fallback to legacy routing if main routing fails
            legacy_payload = {"prompt": user_input, "context": context or {}}
            response = requests.post("http://localhost:8001/legacy/route", json=legacy_payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", str(data))
            
    except Exception as e:
        return f"[Error contacting agentic LLM backend: {e}]"

# --- Notes feature is currently disabled. To re-enable, uncomment the notes_fragment function and its usages below. ---
# @st.fragment
# def notes_fragment():
#     st.subheader("Your Notes")
#     ... (full implementation commented out) ...
#     pass


# --- Chat Feature as Modular Function ---


def chat_fragment():
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "pending_user_input" not in st.session_state:
        st.session_state["pending_user_input"] = ""

    # Chat input box (always at the bottom)
    user_input = st.chat_input("Ask a question about the data, contracts, or trends:", key="chat_input")
    if user_input and user_input.strip() and user_input.strip().lower() != "chat":
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        ai_response = get_agentic_response(user_input)
        st.session_state["chat_history"].append({"role": "ai", "content": ai_response})
        st.session_state["pending_user_input"] = ""
    elif user_input and user_input.strip().lower() == "chat":
        st.warning("Please enter a real question, not just 'chat'.")

    # Display chat history (including the latest response if just submitted)
    for msg in st.session_state["chat_history"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

# --- Main Streamlit Page ---
def main():
    """
    Streamlit page entry point for AI Data Agent.
    Sets up theme, description, and renders chat fragment.
    """
    # Automatic session timeout/soft-delete check
    check_and_handle_session_timeout()
    # Inject custom theme CSS for visual consistency
    st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)
    st.title("🤖 AI Data Agent")
    st.subheader("Chat with the Data")
    
    # Phase 1 status indicator
    try:
        status_response = requests.get("http://localhost:8001/orchestrator/system_status", timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            st.success(f"✅ Phase 1 Active: Dynamic Discovery ({status_data['total_capabilities']} capabilities from {status_data['healthy_servers']}/{status_data['total_servers']} servers)")
        else:
            st.warning("⚠️ Using Legacy Routing (Phase 1 services unavailable)")
    except:
        st.warning("⚠️ Using Legacy Routing (Phase 1 services unavailable)")
    
    st.markdown(
        """
        **Welcome to the AI Data Agent!**

        This page lets you interact with an advanced AI assistant powered by multiple local LLMs running via Ollama. The system uses an "orchestrator" LLM (Llama3.2-8B or Mistral-7B) to interpret your intent and route requests to specialized models for code, visualization, and analysis.

        - **Data Sources:** Capture Insights Database - usaspending_prime_awards and usaspending_subawards tables.
        - **Ollama** runs all models locally for privacy and performance (no external API calls).
        - **Orchestrator LLM** (Llama3.2-8B or Mistral-7B) interprets your question and decides which tool or model to use.
        - **Specialized models** (e.g., CodeLlama, StarCoder2) handle code generation, data queries, and visualizations as needed.
        - **Fine-tuned Models:** The LLMs have been fine-tuned on defense contracting, logistics, and business intelligence data to provide more relevant, actionable insights and context-aware responses.
        - Ask about spending trends, top agencies, expiring contracts, or any other business intelligence question.
        - The AI has access to all available data, not just the current dashboard or filtered view.
        - Use natural language—no need for technical terms or SQL.
        _For context-specific analysis, use the other dashboard pages._
        """
    )
    # notes_fragment()  # Notes feature disabled
    st.markdown("---")
    chat_fragment()

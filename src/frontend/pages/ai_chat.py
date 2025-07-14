import streamlit as st
import time
import requests
import asyncio
import threading
import concurrent.futures
import nest_asyncio
import atexit
import sys
from pathlib import Path
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css
from src.frontend.ai.capture_intelligence_agent import CaptureIntelligenceAgent

# Apply nest_asyncio to allow nested asyncio event loops (required by Streamlit)
nest_asyncio.apply()

# Initialize session state for event loop
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

# Helper function for running async functions
def run_async(coro):
    """Run an async function within the stored event loop."""
    return st.session_state.loop.run_until_complete(coro)

def reset_agent_state():
    """Reset all agent-related session state variables."""
    if hasattr(st.session_state, 'agent') and st.session_state.agent is not None:
        try:
            # Clean up the existing agent properly
            if hasattr(st.session_state.agent, 'cleanup'):
                run_async(st.session_state.agent.cleanup())
        except Exception as e:
            st.error(f"Error cleaning up previous agent: {str(e)}")
    
    st.session_state.agent = None

def on_shutdown():
    """Proper cleanup when the session ends."""
    reset_agent_state()

# Register cleanup logic on program exit
atexit.register(on_shutdown)

# Add project root to path for import
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

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

def check_python_mcp_sdk_status():
    """
    Simple status check for the Python MCP SDK architecture.
    Returns basic status for UI display.
    """
    try:
        # Basic imports check
        import mcp.server
        return {
            "status": "success",
            "message": "Python MCP SDK Available",
            "details": "System ready for MCP operations"
        }
    except ImportError:
        return {
            "status": "error", 
            "message": "Python MCP SDK Not Available",
            "details": "Please install: pip install mcp>=1.0.0"
        }

def get_capture_intelligence_agent():
    """
    Get or create a Capture Intelligence Agent instance with session state caching.
    Handles async initialization properly.
    """
    if "capture_intelligence_agent" not in st.session_state:
        try:
            from src.frontend.ai.capture_intelligence_agent import CaptureIntelligenceAgent
            agent = CaptureIntelligenceAgent()
            st.session_state["capture_intelligence_agent"] = agent
            st.session_state["agent_initialized"] = False
        except Exception as e:
            st.error(f"Failed to initialize Capture Intelligence agent: {e}")
            return None
    
    return st.session_state.get("capture_intelligence_agent")

async def initialize_agent_if_needed(agent):
    """
    Initialize the agent if not already initialized.
    """
    if not st.session_state.get("agent_initialized", False):
        try:
            await agent.initialize()
            st.session_state["agent_initialized"] = True
            return True
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
            return False
    return True

def get_agentic_response(user_input, context=None):
    """
    Get response using Capture Intelligence Agent with Python MCP SDK integration.
    Uses nest_asyncio approach for reliable Streamlit + asyncio integration.
    """
    try:
        # Create a fresh agent for each request to avoid event loop conflicts
        from src.frontend.ai.capture_intelligence_agent import CaptureIntelligenceAgent
        
        # Handle async initialization and chat using nest_asyncio approach
        async def async_chat():
            # Create fresh agent instance
            agent = CaptureIntelligenceAgent()
            
            # Initialize the fresh agent
            await agent.initialize()
            
            # Use the agent for this request
            response = await agent.chat_async(user_input)
            
            # Clean up the agent
            await agent.cleanup() if hasattr(agent, 'cleanup') else None
            
            return response
        
        # Use the nest_asyncio approach for reliable Streamlit + asyncio integration
        return run_async(async_chat())
                
    except Exception as e:
        return f"[Error with Capture Intelligence Agent communication: {e}]"

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
    st.title("🤖 AI Business Development Consultant")
    st.subheader("Natural Conversation with Data")
    
    # Python MCP SDK Architecture Status
    architecture_status = check_python_mcp_sdk_status()
    
    if architecture_status["status"] == "success":
        st.success(f"✅ {architecture_status['message']}: {architecture_status['details']}")
    elif architecture_status["status"] == "warning":
        st.warning(f"⚠️ {architecture_status['message']} - consultant will use general knowledge")
    else:
        st.error(f"❌ {architecture_status['message']} - system not fully available")
    
    st.markdown(
        """
        **Welcome to your AI Business Development Consultant!**

        Roberto, your AI consultant, works as a skilled defense contracting expert with direct access to your capture insights database through a pure Python implementation.

        **The Capture Intelligence Agent Philosophy:**
        Roberto intelligently decides when and how to use database tools. He can handle simple conversations without unnecessary tool usage, but when you need data analysis, he seamlessly connects to your PostgreSQL database through the Python MCP SDK to explore contract data, market intelligence, and competitive insights.

        _Simply ask Roberto any question about defense contracting, market analysis, or business development. He'll intelligently decide whether to use database tools or respond from his expertise._
        """
    )
    # notes_fragment()  # Notes feature disabled
    st.markdown("---")
    chat_fragment()

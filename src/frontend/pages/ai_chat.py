import streamlit as st
import time
import requests
import asyncio
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css
from src.frontend.ai.llamaindex_mcp_communication import LangGraphOrchestratorAgent

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

def check_langchain_agent_status():
    """
    Check if the LangGraph Orchestrator Agent with FastMCP integration is available.
    Performs comprehensive health check including agent initialization.
    """
    try:
        # Check if Ollama is running (required for LLM)
        ollama_response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if ollama_response.status_code != 200:
            return {"status": "error", "message": "Ollama LLM server not available"}
        
        # Check if FastMCP server is responding
        try:
            mcp_response = requests.get("http://localhost:8003/", timeout=3)
            # Any response (including 404) means the server is running
            server_running = True
        except requests.exceptions.ConnectionError:
            server_running = False
        
        if not server_running:
            return {"status": "warning", "message": "FastMCP database server not running"}
        
        # Check if the LangGraph agent is importable and can initialize
        try:
            from src.frontend.ai.llamaindex_mcp_communication import LangGraphOrchestratorAgent
            # Test basic initialization (this is lightweight)
            agent = LangGraphOrchestratorAgent()
            return {
                "status": "success", 
                "message": "LangGraph Agent Architecture Active",
                "details": "Ollama LLM and FastMCP database server ready"
            }
        except ImportError:
            return {"status": "error", "message": "LangGraph Orchestrator Agent not available"}
        except Exception as e:
            return {"status": "error", "message": f"Agent initialization failed: {str(e)[:50]}..."}
        
    except Exception as e:
        return {"status": "error", "message": f"System check failed: {str(e)[:50]}..."}

def get_langchain_agent():
    """
    Get or create a LangGraph Orchestrator Agent instance with session state caching.
    Handles async initialization properly.
    """
    if "langchain_agent" not in st.session_state:
        try:
            from src.frontend.ai.llamaindex_mcp_communication import LangGraphOrchestratorAgent
            agent = LangGraphOrchestratorAgent()
            st.session_state["langchain_agent"] = agent
            st.session_state["agent_initialized"] = False
        except Exception as e:
            st.error(f"Failed to initialize LangGraph agent: {e}")
            return None
    
    return st.session_state.get("langchain_agent")

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
    Get response using LangGraph Orchestrator Agent with FastMCP integration.
    Simplified async handling based on working implementation.
    """
    try:
        # Get the cached agent instance
        agent = get_langchain_agent()
        
        if not agent:
            return "[Error: AI system not properly initialized. Please refresh the page.]"
        
        # Handle async initialization and chat using simplified approach
        async def async_chat():
            # Initialize agent if needed
            if not await initialize_agent_if_needed(agent):
                return "[Error: Agent initialization failed. Please try again.]"
            
            # Use LangGraph Orchestrator Agent for intelligent tool orchestration
            response = await agent.chat_async(user_input)
            return response
        
        # Simplified async execution - just use asyncio.run
        try:
            return asyncio.run(async_chat())
        except Exception as e:
            return f"[Error processing request: {str(e)[:100]}...]"
        
    except Exception as e:
        return f"[Error with LangGraph Agent communication: {e}]"

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
    st.title("🤖 AI Business Intelligence Consultant")
    st.subheader("Natural Conversation with Data")
    
    # LangGraph Agent + FastMCP Architecture Status
    architecture_status = check_langchain_agent_status()
    
    if architecture_status["status"] == "success":
        st.success(f"✅ {architecture_status['message']}: {architecture_status['details']}")
        
        # Add detailed health check button
        if st.button("🔍 Run Detailed Health Check", help="Check agent initialization and tool availability"):
            with st.spinner("Running comprehensive health check..."):
                agent = get_langchain_agent()
                if agent:
                    try:
                        async def run_health_check():
                            await initialize_agent_if_needed(agent)
                            return await agent.health_check()
                        
                        health_info = asyncio.run(run_health_check())
                        
                        st.write("**Health Check Results:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("LLM Status", "✅ Ready" if health_info.get('llm_initialized') else "❌ Failed")
                            st.metric("Agent Status", "✅ Ready" if health_info.get('agent_initialized') else "❌ Failed")
                        
                        with col2:
                            st.metric("Total Tools", health_info.get('total_tools', 0))
                            server_count = len([s for s in health_info.get('mcp_servers', {}).values() if s.get('status') == 'connected'])
                            st.metric("MCP Servers", f"{server_count} connected")
                        
                        # Show detailed server status
                        if health_info.get('mcp_servers'):
                            st.write("**MCP Server Details:**")
                            for server_name, server_info in health_info.get('mcp_servers', {}).items():
                                status = server_info.get('status', 'unknown')
                                if status == 'connected':
                                    st.success(f"🟢 {server_name}: Connected ({server_info.get('tool_count', 0)} tools)")
                                else:
                                    st.error(f"🔴 {server_name}: {status}")
                                    if server_info.get('error'):
                                        st.text(f"   Error: {server_info['error']}")
                        
                    except Exception as e:
                        st.error(f"Health check failed: {e}")
                else:
                    st.error("Could not initialize agent for health check")
    
    elif architecture_status["status"] == "warning":
        st.warning(f"⚠️ {architecture_status['message']} - consultant will use general knowledge")
    else:
        st.error(f"❌ {architecture_status['message']} - system not fully available")
    
    st.markdown(
        """
        **Welcome to your AI Business Intelligence Consultant!**

        This system uses a **revolutionary LangGraph + FastMCP Architecture** where the AI works as a skilled consultant with access to your capture insights database.

        **The LangGraph Agent Philosophy:**
        This AI consultant intelligently decides when and how to use database tools. It can handle simple conversations without unnecessary tool usage, but when you need data analysis, it seamlessly connects to your s3_processed database to explore contract data, market intelligence, and competitive insights.

        **Key Features:**
        - **Intelligent Tool Usage**: Only uses database tools when actually needed
        - **Natural Conversations**: Handles greetings and simple queries without forcing tool usage
        - **Database-Driven Intelligence**: All data insights come from your actual contract database
        - **Real-Time Discovery**: AI explores your database structure and contents dynamically
        - **Strategic Analysis**: Combines database insights with defense contracting expertise
        - **Modern Architecture**: Uses LangGraph for flexible, state-aware agent workflows
        - **FastMCP Integration**: Direct connection to PostgreSQL through MCP protocol

        _Simply ask any question about defense contracting, market analysis, or business development. The AI will intelligently decide whether to use tools or respond from its knowledge base._
        """
    )
    # notes_fragment()  # Notes feature disabled
    st.markdown("---")
    chat_fragment()

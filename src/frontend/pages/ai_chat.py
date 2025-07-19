"""
AI Chat Interface - Simplified

Streamlined Streamlit interface for the Capture Intelligence Agent.
Eliminates complex session management and focuses on clean chat experience.

Key simplifications:
- Single agent instance with automatic initialization
- Clean session state management
- Proper error handling with user feedback
- Agent status monitoring
"""

import streamlit as st
import asyncio
import nest_asyncio
import atexit
import logging
import time
from pathlib import Path
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import agent
from src.frontend.ai.capture_intelligence_agent import get_agent

# Import theme
from src.frontend.styles.theme import THEME
from src.frontend.styles.custom_css import generate_theme_css

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply theme
st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)

# Global thread pool for async operations
_thread_pool = ThreadPoolExecutor(max_workers=4)

# --- Asyncio/Streamlit event loop fix ---
nest_asyncio.apply()

# Initialize session state for event loop
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

def run_async(coro):
    """Run async coroutine in a thread-safe way for Streamlit."""
    """Run an async function within the stored event loop."""
    return st.session_state.loop.run_until_complete(coro)

# Optional: Cleanup logic for agent/client shutdown (if needed)
def on_shutdown():
    if "agent" in st.session_state and st.session_state.agent is not None:
        try:
            if hasattr(st.session_state.agent, "cleanup"):
                run_async(st.session_state.agent.cleanup())
        except Exception as e:
            st.error(f"Error during shutdown: {str(e)}")
atexit.register(on_shutdown)

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent_ready" not in st.session_state:
        st.session_state.agent_ready = False
    if "agent_status" not in st.session_state:
        st.session_state.agent_status = "initializing"
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = None

async def get_agent_status():
    """Get current agent status."""
    try:
        agent = await get_agent()
        status = await agent.get_tool_status()
        return status
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return {"status": "error", "error": str(e)}

async def chat_with_agent(user_input: str) -> str:
    """Send message to agent and get response."""
    try:
        agent = await get_agent()
        # Pass the full conversation history for multi-turn chat
        history = st.session_state.get("messages", [])
        # Clear debug info before each call
        st.session_state.debug_info = None
        response, debug_info = await agent.chat_async(user_input, history=history, debug=True)
        st.session_state.debug_info = debug_info
        return response
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        st.session_state.debug_info = {"error": str(e)}
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."

def display_agent_status():
    """Display agent status in sidebar."""
    with st.sidebar:
        st.header("🤖 Agent Status")
        
        # Get status using thread-safe async execution
        status = run_async(get_agent_status())
        
        if status["status"] == "healthy":
            st.success("✅ Agent Ready")
            st.info(f"🔧 Tools Available: {status.get('total_tools', 0)}")
            
            # Show tool details
            with st.expander("Tool Details"):
                for tool in status.get("available_tools", []):
                    st.write(f"• **{tool['name']}**: {tool['description']}")
                    
        elif status["status"] == "degraded":
            st.warning("⚠️ Agent Running (Limited)")
            st.info("Some tools may not be available")
            
        elif status["status"] == "error":
            st.error("❌ Agent Error")
            st.error(status.get("error", "Unknown error"))
            
        else:
            st.info("🔄 Agent Initializing...")

def main():
    """Main chat interface."""
    # Initialize session state
    initialize_session_state()
    
    # Page header and welcome
    st.title("🤖 AI Business Development Consultant")
    st.markdown("""
**Welcome to your AI Business Development Consultant!**

This system features Roberto, an expert AI agent specializing in defense contracting and business development, with direct access to your capture insights database.

**The Capture Intelligence Agent Philosophy:**
Roberto responds conversationally and only uses database tools when needed. For simple questions, he answers from expertise; for data-driven analysis, he seamlessly connects to your database to provide contract data, market intelligence, and competitive insights.

_Ask Roberto anything about defense contracting, market analysis, or business development. He will intelligently decide when to use database tools or respond from his expertise._
    """)
    
    # Display agent status
    display_agent_status()

    # Debug toggle in sidebar
    with st.sidebar:
        show_debug = st.checkbox("Show Debug Info", value=False)
    
    # Chat interface
    st.subheader("💬 Chat")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask me about contract data..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_async(chat_with_agent(prompt))
                st.markdown(response)

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Debug info display in sidebar
    if show_debug and st.session_state.debug_info:
        with st.sidebar.expander("LLM Tool Debug Info", expanded=True):
            st.write(st.session_state.debug_info)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Tips**: "
        "Ask about contract trends, competitor analysis, or specific opportunities. "
        "I can query database information and provide strategic insights."
    )

if __name__ == "__main__":
    main()

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
import logging
import time
from pathlib import Path
import sys

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

# Page configuration
st.set_page_config(
    page_title="AI Chat - Data Insights",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme
st.markdown(generate_theme_css(THEME), unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent_ready" not in st.session_state:
        st.session_state.agent_ready = False
    if "agent_status" not in st.session_state:
        st.session_state.agent_status = "initializing"

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
        response = await agent.chat_async(user_input)
        return response
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."

def display_agent_status():
    """Display agent status in sidebar."""
    with st.sidebar:
        st.header("🤖 Agent Status")
        
        # Get status asynchronously
        status = asyncio.run(get_agent_status())
        
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
    
    # Page header
    st.title("🤖 AI Chat - Defense Contract Intelligence")
    st.markdown("Ask me about contract data, competitive intelligence, or capture strategy.")
    
    # Display agent status
    display_agent_status()
    
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
                response = asyncio.run(chat_with_agent(prompt))
                st.markdown(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
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
